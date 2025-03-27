from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import atexit
import argparse
from datetime import datetime

def get_args():
    parser = argparse.ArgumentParser(description='Snapshot VMs on ESXi')
    parser.add_argument('--host', required=True, help='ESXi host/IP')
    parser.add_argument('--user', required=True, help='ESXi username')
    parser.add_argument('--password', required=True, help='ESXi password')
    return parser.parse_args()

def get_all_vms(content):
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    return container.view

def create_snapshot(vm, name, description):
    task = vm.CreateSnapshot_Task(
        name=name,
        description=description,
        memory=False,
        quiesce=False
    )
    return task

def wait_for_task(task):
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        continue
    if task.info.state == vim.TaskInfo.State.success:
        return True
    else:
        raise task.info.error

def main():
    args = get_args()

    # Skip SSL cert verification
    context = ssl._create_unverified_context()

    # Connect to ESXi or vCenter
    si = SmartConnect(
        host=args.host,
        user=args.user,
        pwd=args.password,
        sslContext=context
    )
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()
    vms = get_all_vms(content)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for vm in vms:
        snap_name = f"AutoSnap_{timestamp}"
        snap_desc = f"Snapshot created by script on {timestamp}"
        print(f"Creating snapshot for VM: {vm.name}")
        try:
            task = create_snapshot(vm, snap_name, snap_desc)
            wait_for_task(task)
            print(f"Snapshot created for {vm.name}")
        except Exception as e:
            print(f"Failed to snapshot {vm.name}: {e}")

if __name__ == '__main__':
    main()
