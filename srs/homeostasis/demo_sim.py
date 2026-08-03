"""Quick demo. Run: python demo_sim.py from this directory."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from service import HomeostasisService
from events import EventID

def main():
    svc = HomeostasisService()
    print("=== idle 50 ===")
    for _ in range(50):
        svc.on_heartbeat()
    print(svc.snapshot())

    print("\n=== work rhythm ===")
    svc = HomeostasisService()
    for t in range(24):
        if (t + 1) % 8 == 0:
            svc.on_event(EventID.EXEC_TASK_DONE)
        elif (t + 1) % 3 == 0:
            svc.on_event(EventID.EXEC_STEP_OK)
        else:
            svc.on_heartbeat()
    print(svc.snapshot())

    print("\n=== crisis ===")
    svc = HomeostasisService()
    svc.on_event(EventID.RES_TOKENS_EXHAUSTED)
    svc.on_event(EventID.EXEC_LOOP_DETECTED)
    print("after crisis", svc.last_snapshot.to_dict())
    svc.on_event(EventID.OUT_BLOCK_CLEARED)
    svc.on_event(EventID.EXEC_TASK_DONE)
    for _ in range(10):
        svc.on_heartbeat()
    print("after recovery", svc.snapshot())

    print("\n=== deferred rules ===")
    svc = HomeostasisService()
    svc.defer("INFO_RULES", importance=0.8, soft_deadline=12.0, note="exchange rules")
    for _ in range(25):
        svc.on_heartbeat()
    print(svc.snapshot())
    svc.complete_deferred()
    print("after done", svc.snapshot())

    print("\n=== idle_tick API ===")
    print(HomeostasisService().idle_tick())

if __name__ == "__main__":
    main()
