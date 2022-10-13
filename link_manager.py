import uuid,json,os,logging

NAMESPACE_PATH = "namespace.txt"
def get_namespace(filename=NAMESPACE_PATH):
    namespace = None
    if os.path.isfile(filename):
        with open(filename) as f:
            try:
                namespace = uuid.UUID(f.read())
            except Exception:
                loggin.info(str(f.read()))
                logging.error('Failed load UUID, making a new one.')
    if namespace is None:
        namespace = uuid.uuid4()
        with open(filename,'w+') as f:
            f.write(str(namespace))
    return namespace

def get_uuids(filename=NAMESPACE_PATH,N=10):
    namespace=get_namespace(filename)
    return [uuid.uuid5(namespace,str(i)) for i in range(N)]

def generate_links(round,N=1_000):
    prefix = "https://survey.gradstudent.me/login?transaction_id="
    ids = get_uuids(filename=f"round_{round}.txt",N=1_000)
    links = [prefix+str(_id) for _id in ids]
    with open(f"round_{round}_tokens.txt","w+") as f:
        f.write('\n'.join([str(i) for i in ids]))
    with open(f"round_{round}_links.txt",'w+') as f:
        f.write('\n'.join(links))

if __name__=="__main__":
    generate_links(round=1)
