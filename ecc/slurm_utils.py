import re

import kbr.run_utils as run_utils
import kbr.datetime_utils as datetime_utils
import kbr.log_utils as logger

def available() -> bool:
    try:
        run = run_utils.launch_cmd( "sinfo" )
        if run.p_status:
            return False

        return True
    except:
        return False




def jobs(partition:str=None):
    #"%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
    #JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
    #33187 usegalaxy     test sysadmin  R       0:15      1 slurm.usegalaxy.no
    cmd = "squeue -hl"

    if partition is not None:
        cmd += f' -p {partition}'


    run = run_utils.launch_cmd( cmd )

#    run = "  33187 usegalaxy     test sysadmin  PD       0:15      1 slurm.usegalaxy.no\n 33187 usegalaxy     test sysadmin  R       0:15      1 slurm.usegalaxy.no"



    run = run.stdout
    if run == b'':
        return []

    run = run.decode('utf-8')


    jobs = []
    for line in run.split("\n"):
        if line == '':
            continue
        fields = line.split()
        jobs.append({"id": fields[0], "user": fields[3], "state":fields[4], "time": fields[5]})

    return jobs

def jobs_pending(partition=None):
    count = 0
    for job in jobs(partition):
        if job['state'] == 'PD' or job['state'] == 'PENDING':
            count += 1

    return count

def pending_time(partition:str=None) -> dict:
    #STATE               PENDING_TIME        
    #PENDING             2454                
    #RUNNING             2451    


#    cmd = "squeue -O state,pendingtime -h"
    cmd = "squeue -O state,SubmitTime -h"

    if partition is not None:
        cmd += f' -p {partition}'

    run = run_utils.launch_cmd( cmd )

    run = run.stdout

    run = run.decode('utf-8')
    pending_times = []
    all_pending_times = []
    max_wait     = -1
    pending_wait = -1
    avg_wait     = -1
    all_avg_wait = -1

    for line in run.split("\n"):
        if line == '':
            continue
        fields = line.split()
        pending_time = (datetime_utils.now() - datetime_utils.to_datetime(fields[1])).seconds
        all_pending_times.append( pending_time )
        if fields[0] == 'PENDING':
            pending_times.append(pending_time)

    if pending_times != []:
        max_wait = max(pending_times)
        pending_wait  = len(pending_times)
        if pending_wait > 0:
            avg_wait = sum( pending_times)/pending_wait

    if all_pending_times != []:
        all_wait = len(all_pending_times)
        if all_wait > 0:
            all_avg_wait = sum( all_pending_times)/all_wait

    return {'max':max_wait, 'pending': pending_wait, 'pending_mean': avg_wait, 'all_mean': all_avg_wait}



def jobs_running():
    count = 0
    for job in jobs():
        if job['state'] == 'R' or job['state'] == 'RUNNING':
            count += 1

    return count

def job_counts_by_state():
    counts = {}
    for job in jobs():

        if job['state'] not in counts:
            counts[ job['state'] ] = 1
        else:
            counts[ job['state'] ] += 1

    return counts



def nodes(partition:str=None):
    #PARTITION             AVAIL  TIMELIMIT  NODES  STATE NODELIST
    #usegalaxy_production*    up   infinite      2    mix nrec1.usegalaxy.no,slurm.usegalaxy.no
    #usegalaxy_production*    up   infinite      1   idle nrec2.usegalaxy.no
    #State of the nodes.  Possible states include: allocated, completing, down, drained, draining, fail, failing, future, idle, maint, mixed, perfctrs, power_down, power_up, reserved, and unknown plus Their abbreviated forms: alloc, comp, down, drain, drng, fail, failg, futr, idle, maint, mix, npc,  pow_dn,  pow_up,
    #               resv, and unk respectively.  Note that the suffix "*" identifies nodes that are presently not responding.
    #ecc-large-3      1    azure* idle* 
    #ecc-node-1       1    azure* idle  
    #ecc-node-2       1    azure* down* 
    cmd = "sinfo -Nh"

    if partition is not None:
        cmd += f" --partition {partition}"

    run = run_utils.launch_cmd( cmd )

#    run = " usegalaxy_production*    up   infinite      2    mix nrec1.usegalaxy.no,slurm.usegalaxy.no\n  usegalaxy_production*    up   infinite      1   alloc nrec2.usegalaxy.no"

    run = run.stdout
    if run == b'':
        return []

    run = run.decode('utf-8')

    nodes = []
    for line in run.split("\n"):
        if line == '':
            continue
        fields = line.split()
        fields[2] = fields[2].replace("*", "")
        nodes.append({'name':fields[0], 'avail': fields[1], "state": fields[3], "partition": fields[2]})
#        for node in fields[5].split(","):
#            nodes.append( {'name':node, 'avail': fields[2], "state": fields[4]})

    return nodes


def node_names() -> list:
    names = []
    for node in nodes():
        names.append(node['name'])

    return names


def nodes_idle():
    count = 0
    for node in nodes():
        if node['state'] in ['mix', 'idle']:
            count += 1

    return count


def nodes_total():
    count = 0
    for _ in nodes():
        count += 1

    return count


def _show_node(id:str) -> str:
    cmd = 'scontrol show node={id}'
    run = run_utils.launch_cmd( cmd )
    return run.stdout

def node_state(id:str) -> str:
    info = _show_node(id)
    for line in info.split('\n'):
#        State=IDLE
        state = re.match(r'State=(w+)', line)
        logger.debug(f"Node state: {state}")
        if state:
            return state

    return None


def node_cpu_info(id:str) -> dict:

    info = _show_node(id)
    for line in info.split('\n'):
        cpus = re.match(r'CPUAlloc=(\d+) CPUTot=(\d+) CPULoad=(\d+.\d\d)', line)
        logger.debug(f"CPUs: {cpus}")
        if cpus:
            return cpus


    return None



def free_resources():
    node_list = nodes()

    cpus_total = 0
    cpus_free  = 0

    for node in node_list:
        cpu_free, cpu_total  = node_cpu_info( node['id'])

        cpus_free  += cpu_free
        cpus_total += cpu_total


    return cpus_free, cpus_total


def add_cloud_node(name, ip_address):
    cmd = f"scontrol update nodename={name} nodeaddr={ip_address} nodehostname={name}"
    run = run_utils.launch_cmd( cmd )


def update_node_state(name, state:str='idle'):
    cmd = f"scontrol update nodename={name} state={state}"
    r = run_utils.launch_cmd( cmd )
    if r.p_status != 0:

        logger.critical( f"scontrol error: {cmd} -- {r.stderr}")
        raise RuntimeError


def set_node_down(name:str):
    update_node_state(name, 'down')

def set_node_drain(name:str):
    update_node_state(name, 'draining')

def set_node_resume(name:str):
    update_node_state(name, 'resume')


def suspend_node(name):
    cmd = f"scontrol update nodename={name} state=down"
    run = run_utils.launch_cmd( cmd )
