import os
from dotenv import load_dotenv
load_dotenv(override=True)

DEPT_NAMES_LOWER = {
    'civil engineering','civil engg.','civil engg','civil',
    'mechanical engineering','mechanical engg.','mechanical engg','mech','mechanical',
    'electrical engineering','electrical engg.','electrical engg','eee','electrical',
}

def matches(val):
    return bool(val and val.strip().lower() in DEPT_NAMES_LOWER)

from pymongo import MongoClient
client = MongoClient(os.getenv('MONGO_URI'), serverSelectionTimeoutMS=8000, tlsInsecure=True)
client.server_info()
db = client.get_default_database()
print('Connected to MongoDB Atlas.')

SET_OP  = "$set"
IN_OP   = "$in"

# 1. Users
users = [u for u in db['users'].find({'role': 'dept'}) if matches(u.get('department', ''))]
if users:
    db['users'].delete_many({'_id': {IN_OP: [u['_id'] for u in users]}})
    print('Deleted users:', [u.get('username') for u in users])
else:
    print('Users: no matches for Civil/Mechanical/Electrical.')

# 2. Departments
depts = [d for d in db['departments'].find({}) if matches(d.get('name', ''))]
if depts:
    db['departments'].delete_many({'_id': {IN_OP: [d['_id'] for d in depts]}})
    print('Deleted departments:', [d.get('name') for d in depts])
else:
    print('Departments: no matches.')

# 3. Registrations
regs = [r for r in db['registrations'].find({}) if matches(r.get('department', ''))]
if regs:
    db['registrations'].delete_many({'_id': {IN_OP: [r['_id'] for r in regs]}})
    print('Deleted registrations:', len(regs))
else:
    print('Registrations: no matches.')

# 4. Scores
scrs = [s for s in db['scores'].find({}) if matches(s.get('department', ''))]
if scrs:
    db['scores'].delete_many({'_id': {IN_OP: [s['_id'] for s in scrs]}})
    print('Deleted scores:', len(scrs))
else:
    print('Scores: no matches.')

# 5. Results — strip standings belonging to those departments
mod = 0
deld = 0
for r in db['results'].find({}):
    orig = r.get('standings', [])
    clean = [s for s in orig if not matches(s.get('department', ''))]
    if len(clean) != len(orig):
        if clean:
            db['results'].update_one({'_id': r['_id']}, {SET_OP: {'standings': clean}})
            mod += 1
        else:
            db['results'].delete_one({'_id': r['_id']})
            deld += 1

print('Results modified=%d, deleted=%d' % (mod, deld))
print('=== CLEANUP COMPLETE ===')
