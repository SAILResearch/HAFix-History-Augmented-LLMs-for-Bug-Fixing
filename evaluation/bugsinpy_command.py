import os
import subprocess
import time


def bugsinpy_checkout(project_name, bug_id) -> bool:
    # if ti success, it always has "Removing bugsinpy_run_test.sh"
    # FNULL = open(os.devnull, 'w')
    # command = "bugsinpy-checkout -p " + project_name + " -i " + bug_id
    print("start checkout...")
    p = subprocess.Popen(["bugsinpy-checkout", "-p", project_name, "-i", bug_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # p = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # p = subprocess.Popen([command], shell=True, stdout=FNULL, stderr=FNULL)
    out, _ = p.communicate()
    print(f"{out.decode()}")
    print("finish checkout...\n\n")
    # p.wait()
    if "Removing bugsinpy_run_test.sh" in str(out):
        return True
    return True


def bugsinpy_compile(project_dir) -> bool:
    os.chdir(project_dir)
    print("start compile...")
    print(f"current work dir is: {os.getcwd()}")
    # if wrong, it always has "This is not a checkout project folder"
    p = subprocess.Popen(["bugsinpy-compile"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = p.communicate()
    print(f"{out.decode()}")
    print("finish compile...\n\n")
    if "This is not a checkout project folder" in str(out):
        return False
    return True


def bugsinpy_test(project_dir) -> bool:
    os.chdir(project_dir)
    print("start test...")
    print(f"current work dir is: {os.getcwd()}")
    # p = subprocess.Popen(["bugsinpy-test"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # out, err = p.communicate()
    out, err = command_with_timeout(["bugsinpy-test"], timeout=120)
    print(f"{out.decode()}")
    print("finish test...\n\n")
    # if there are 1 passed and 1 failed, it will return False
    # unittest return "FAILED" or "OK"
    # pytest return "failed" or "passed"
    if "FAILED" in str(out) or "failed" in str(out):
        return False
    if "passed" in str(out) or "OK" in str(out):
        return True
    # It is possible return something like "module is not found"
    return False


def command_with_timeout(cmd, timeout=300):
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    t_beginning = time.time()
    while True:
        if p.poll() is not None:
            break
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            p.terminate()
            return 'TIMEOUT', 'TIMEOUT'
        time.sleep(1)
    out, err = p.communicate()
    return out, err
