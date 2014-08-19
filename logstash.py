import requests

LOGSTASH = 'http://localhost:9100/jolokia/read/java.lang:type=Memory'


def main():
    r = requests.get(LOGSTASH)
    if not r.ok:
        print 'status err received status code {0}'.format(r.status_code)
        raise SystemExit(True)

    json = r.json()
    if json['status'] != 200:
        print 'status err JSON had status {0} instead of 200'.format(
            json['status']
        )
        raise SystemExit(True)

    non_heap = json['value']['NonHeapMemoryUsage']
    heap = json['value']['HeapMemoryUsage']
    print 'status ok'
    print_memory_usage('non_heap', non_heap)
    print_memory_usage('heap', heap)


def print_memory_usage(prefix, mem_dict):
    for (k, v) in mem_dict.items():
        print 'metric {0}_mem_usage_{1} uint32 {2}'.format(prefix, k, v)


if __name__ == '__main__':
    main()
