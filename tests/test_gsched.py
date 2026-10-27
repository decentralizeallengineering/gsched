"""Smoke tests for gsched with a fake nvidia-smi: placement, queueing, release, preemption of a restartable booking, and hwq."""
import importlib.machinery, importlib.util, os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")


def load():
    loader = importlib.machinery.SourceFileLoader("gsched_mod", os.path.join(BIN, "gsched"))
    spec = importlib.util.spec_from_loader("gsched_mod", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        smi = os.path.join(t, "smi")
        with open(smi, "w") as f:
            f.write("#!/bin/sh\necho '0, GPU-aaa, Example GPU, 8192'\n")
        os.chmod(smi, 0o755)
        with open(os.path.join(t, "gsched.conf"), "w") as f:
            f.write("high=1\nlow=3\n")
        os.environ.update(GSCHED_DIR=t, GSCHED_SMI=smi, GSCHED_SYSTEMCTL="true")
        os.environ.pop("GSCHED_CONF", None)
        self.g = load()

    def tearDown(self):
        self.tmp.cleanup()

    def test_queue_and_release(self):
        m1, b1 = self.g.book("low", "", "", 30, 0, "any", False, False, None)
        self.assertEqual(b1["state"], "active")
        m2, b2 = self.g.book("low", "", "", 30, 4, "any", False, False, None)
        self.assertEqual(b2["state"], "queued")
        self.g.release(b1["id"])
        self.assertEqual(self.g.get(self.g.db(), b2["id"])["state"], "active")

    def test_unknown_role_refused(self):
        with self.assertRaises(self.g.Refuse):
            self.g.book("nobody", "", "", 30, 0, "any", False, False, None)

    def test_preempt_restartable(self):
        _, low = self.g.book("low", "", "", 30, 0, "any", False, True, None)
        _, high = self.g.book("high", "", "", 30, 0, "any", False, False, None)
        st = self.g.db()
        self.assertEqual(st["b"][str(high["id"])]["state"], "active")
        self.assertEqual(st["b"][str(low["id"])]["state"], "queued")

    def test_hwq_help_and_role_check(self):
        out = subprocess.run([os.path.join(BIN, "hwq"), "--help"], capture_output=True, text=True, timeout=20)
        self.assertEqual(out.returncode, 0)
        env = dict(os.environ, GSCHED_ROLE="")
        out = subprocess.run([os.path.join(BIN, "hwq"), "gpu0", "x", "--", "true"], capture_output=True, text=True, env=env, timeout=20)
        self.assertEqual(out.returncode, 4)


if __name__ == "__main__":
    unittest.main()
