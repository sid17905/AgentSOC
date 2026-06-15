import asyncio
from dataclasses import asdict, dataclass
from typing import Awaitable, Callable, Optional

from backend.config import utc_now
from backend.schemas import AgentInput, InputType


SubmitIncident = Callable[[AgentInput], Awaitable[dict]]


MOCK_EVENTS = [
    (
        "mock-siem-bruteforce.log",
        """\
Jun 14 11:40:01 auth-01 sshd[4021]: Failed password for admin from 198.51.100.23 port 51992 ssh2
Jun 14 11:40:06 auth-01 sshd[4028]: Failed password for root from 198.51.100.23 port 51998 ssh2
Jun 14 11:40:12 auth-01 sshd[4036]: Failed password for svc-backup from 198.51.100.23 port 52005 ssh2
Jun 14 11:40:18 auth-01 sshd[4041]: Accepted password for svc-backup from 198.51.100.23 port 52010 ssh2
Jun 14 11:40:31 fw-edge-01 firewall[8831]: ALERT brute_force src=198.51.100.23 dst=10.0.4.12 service=ssh failed_count=7 action=allowed
""",
    ),
    (
        "mock-edr-ransomware.log",
        """\
Jun 14 11:42:03 edr-02 sensor[9912]: process powershell.exe spawned suspicious child encryptor.exe on host finance-ws-07
Jun 14 11:42:06 edr-02 sensor[9912]: high file rename volume detected path=C:\\Users\\finance\\Documents extension=.locked count=184
Jun 14 11:42:11 edr-02 sensor[9912]: outbound connection to 185.220.101.5:443 reputation=malicious process=encryptor.exe
Jun 14 11:42:20 edr-02 sensor[9912]: ransomware behavior score=94 host=finance-ws-07 user=j.singh
""",
    ),
    (
        "mock-mail-phishing.eml",
        """\
From: payroll-support@example-login.invalid
To: accounts@example.com
Subject: Urgent payroll verification required

Your payroll account will be suspended today. Verify your account immediately:
https://example-login.invalid/payroll/verify

Headers: SPF=fail DKIM=none DMARC=fail Source-IP=203.0.113.77
""",
    ),
    (
        "mock-dlp-exfiltration.log",
        """\
Jun 14 11:45:44 proxy-01 dlp[4411]: large upload detected user=analyst2 dst=fileshare.example.net bytes=734003200
Jun 14 11:45:46 proxy-01 dlp[4411]: sensitive pattern match type=customer_records count=1294
Jun 14 11:45:49 proxy-01 firewall[9244]: outbound transfer src=10.0.8.21 dst=192.0.2.88 port=443 action=allowed
Jun 14 11:46:01 iam-01 auth[8142]: unusual access token use user=analyst2 country=unknown
""",
    ),
]


@dataclass
class MockIngestionStatus:
    running: bool = False
    produced_count: int = 0
    interval_seconds: float = 30.0
    limit: Optional[int] = 8
    last_filename: Optional[str] = None
    last_incident_id: Optional[str] = None
    last_error: Optional[str] = None
    last_ingested_at: Optional[str] = None


class MockIngestionRunner:
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._event_index = 0
        self._status = MockIngestionStatus()

    def status(self) -> dict:
        if self._task and self._task.done():
            self._status.running = False
        return asdict(self._status)

    async def ingest_once(self, submit: SubmitIncident) -> dict:
        agent_input = self._next_agent_input()
        try:
            result = await submit(agent_input)
            self._status.produced_count += 1
            self._status.last_filename = agent_input.filename
            self._status.last_incident_id = result.get("incident_id")
            self._status.last_error = None
            self._status.last_ingested_at = utc_now().isoformat()
            return {
                "source": "mock",
                "filename": agent_input.filename,
                "incident_id": self._status.last_incident_id,
            }
        except Exception as exc:
            self._status.last_error = str(exc)
            raise

    async def _ingest_specific(self, submit: SubmitIncident, index: int) -> dict:
        """Ingest a specific MOCK_EVENT by index without advancing the shared pointer."""
        filename, content = MOCK_EVENTS[index]
        stamped_content = (
            f"# mock_source=auto-boot filename={filename} "
            f"generated_at={utc_now().isoformat()}\n"
            f"{content}"
        )
        input_type = InputType.EMAIL if filename.endswith(".eml") else InputType.LOG
        agent_input = AgentInput(
            input_type=input_type,
            content=stamped_content,
            filename=filename,
        )
        try:
            result = await submit(agent_input)
            self._status.produced_count += 1
            self._status.last_filename = agent_input.filename
            self._status.last_incident_id = result.get("incident_id")
            self._status.last_error = None
            self._status.last_ingested_at = utc_now().isoformat()
            return {
                "source": "mock-boot",
                "filename": agent_input.filename,
                "incident_id": self._status.last_incident_id,
            }
        except Exception as exc:
            self._status.last_error = str(exc)
            raise

    async def auto_start(self, submit: SubmitIncident) -> None:
        """
        Called once at server startup.
        Ingests ALL mock event types in parallel so the feed is
        pre-populated the moment the UI loads.
        A short stagger (0.3 s between each) avoids DB write collisions.
        """
        print("[MockIngestion] Auto-seeding all mock events on startup...")
        self._status.running = True

        async def _staggered(index: int) -> None:
            await asyncio.sleep(index * 0.3)
            try:
                result = await self._ingest_specific(submit, index)
                print(
                    f"[MockIngestion] Seeded [{index+1}/{len(MOCK_EVENTS)}] "
                    f"{result['filename']} → {result['incident_id']}"
                )
            except Exception as exc:
                print(f"[MockIngestion] Seed failed for index {index}: {exc}")

        await asyncio.gather(*[_staggered(i) for i in range(len(MOCK_EVENTS))])
        self._status.running = False
        print(
            f"[MockIngestion] Auto-seed complete. "
            f"{self._status.produced_count} incidents created."
        )

    def start(
        self,
        submit: SubmitIncident,
        interval_seconds: float = 15.0,
        limit: Optional[int] = None,
    ) -> dict:
        if self._task and not self._task.done():
            return self.status()

        self._status.running = True
        self._status.interval_seconds = max(interval_seconds, 1.0)
        self._status.limit = limit
        self._status.last_error = None
        self._task = asyncio.create_task(self._run(submit))
        return self.status()

    async def stop(self) -> dict:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._status.running = False
        return self.status()

    async def _run(self, submit: SubmitIncident) -> None:
        produced_in_run = 0
        try:
            while self._status.limit is None or produced_in_run < self._status.limit:
                await self.ingest_once(submit)
                produced_in_run += 1
                await asyncio.sleep(self._status.interval_seconds)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._status.last_error = str(exc)
        finally:
            self._status.running = False

    def _next_agent_input(self) -> AgentInput:
        filename, content = MOCK_EVENTS[self._event_index % len(MOCK_EVENTS)]
        self._event_index += 1
        stamped_content = (
            f"# mock_source=mock-ingestion filename={filename} "
            f"generated_at={utc_now().isoformat()}\n"
            f"{content}"
        )
        input_type = InputType.EMAIL if filename.endswith(".eml") else InputType.LOG
        return AgentInput(
            input_type=input_type,
            content=stamped_content,
            filename=filename,
        )


mock_ingestion = MockIngestionRunner()