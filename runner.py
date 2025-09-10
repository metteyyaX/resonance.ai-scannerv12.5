# runner.py
import os, signal, subprocess, sys, time

PY = sys.executable
PORT = os.environ.get("PORT", "8080")

PROCS = [
    [PY, "top50finder_v_2_3.py"],          # Top50 (REST → universe.latest.jsonl)
    [PY, "resonance_scannerv13_3_ws.py"],  # Scanner (WS → detections + Discord)
    ["gunicorn", "-w", "1", "-b", f"0.0.0.0:{PORT}", "serve_detections:app"],
]

def start(cmd):
    env = os.environ.copy()
    env["PORT"] = PORT
    print(f"[runner] starting: {' '.join(cmd)}", flush=True)
    return subprocess.Popen(cmd, env=env)

def main():
    procs = [start(cmd) for cmd in PROCS]

    def shutdown(*_):
        print("[runner] shutting down…", flush=True)
        for p in procs:
            try: p.terminate()
            except: pass
        for p in procs:
            try: p.wait(timeout=6)
            except: pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        for i, p in enumerate(procs):
            ret = p.poll()
            if ret is not None:
                print(f"[runner] process exited ({ret}); restarting: {' '.join(PROCS[i])}", flush=True)
                procs[i] = start(PROCS[i])
        time.sleep(2)

if __name__ == "__main__":
    main()
