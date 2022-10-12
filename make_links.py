import uuid,json

output = {}
_id="iota"
prefix = "https://survey.gradstudent.me/login?transaction_id="
for i in range(1_000):
    key = f"{_id}{i}"
    uid = str(uuid.uuid4())+key
    output={
        uid: key
    }
    print(prefix+uid)
json.dump(output,open("uids_{_id}.json",'w+'))
