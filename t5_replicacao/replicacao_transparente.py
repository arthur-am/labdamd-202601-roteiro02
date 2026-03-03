import random
from typing import List
from dataclasses import dataclass, field

class FakeConnection:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def execute(self, sql: str) -> list:
        host = self.dsn.split("@")[-1]
        print(f"  [query em {host}]: {sql}")
        return [{"result": "ok"}]

def connect(dsn: str) -> FakeConnection:
    if "bad" in dsn:
        raise ConnectionError(f"Replica indisponivel: {dsn}")
    return FakeConnection(dsn)

@dataclass
class ReplicaPool:
    master_dsn: str
    replica_dsns: List[str] = field(default_factory=list)
    _healthy: List[str] = field(default_factory=list, init=False)

    def __post_init__(self):
        self._healthy = list(self.replica_dsns)

    def _pick_replica(self) -> str:
        return random.choice(self._healthy) if self._healthy else self.master_dsn

    def query(self, sql: str, write: bool = False) -> list:
        dsn = self.master_dsn if write else self._pick_replica()
        try:
            conn = connect(dsn)
            return conn.execute(sql)
        except ConnectionError as e:
            print(f"  [aviso] {e} — usando master como fallback.")
            if dsn in self._healthy:
                self._healthy.remove(dsn)
            if not write:
                conn = connect(self.master_dsn)
                return conn.execute(sql)
            raise

pool = ReplicaPool(
    master_dsn="postgresql://app@master:5432/app",
    replica_dsns=[
        "postgresql://app@replica1:5432/app",
        "postgresql://app@bad-replica:5432/app",
        "postgresql://app@replica2:5432/app",
    ]
)

print("=== Leituras (com balanceamento entre replicas) ===")
for i in range(5):
    pool.query(f"SELECT * FROM users WHERE id={i + 1}")

print("\n=== Escrita (sempre no master) ===")
pool.query("INSERT INTO logs VALUES ('evento')", write=True)

print(f"\nReplicas saudaveis restantes: {len(pool._healthy)}")