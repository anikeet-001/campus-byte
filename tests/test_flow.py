import os
import tempfile
import unittest
from fastapi.testclient import TestClient
from backend.main import app

class CampusFlow(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        from unittest.mock import patch
        env = patch.dict(os.environ, DB_PATH=temp.name+'/test.sqlite', JWT_SECRET='x'*48)
        env.start()
        self.addCleanup(env.stop)
        self.http = self.enterContext(TestClient(app))
        self.customer = self.register('customer','alice')
        self.owner = self.register('owner','kitchen')
        self.place = self.http.get('/api/restaurants').json()[0]['id']
        self.dish = self.http.post('/api/menu',headers=self.owner,json={'name':'Poha','paise':4000}).json()['id']

    def register(self, role, name):
        response = self.http.post('/api/register',json={'role':role,'email':name+'@campus.test','name':name,
            'password':'demo-test-pass','restaurant':name if role=='owner' else None})
        self.assertEqual(response.status_code,201,response.text)
        return {'Authorization':'Bearer '+response.json()['token']}

    def order(self):
        response = self.http.post('/api/orders',headers=self.customer,json={'restaurant':self.place,'address':'Hostel A, 105',
            'items':[{'dish':self.dish,'quantity':2}]})
        self.assertEqual(response.status_code,201,response.text)
        self.assertEqual(response.json()['total'],8000)
        return response.json()['id']

    def act(self, order, action, headers):
        return self.http.post(f'/api/orders/{order}/{action}',headers=headers)

    def recent(self, headers):
        return self.http.get('/api/orders',headers=headers).json()

    def test_dispatch_queue_and_delivery(self):
        first, second = self.order(), self.order()
        for key in (first,second):
            self.assertEqual(self.act(key,'accept',self.owner).status_code,200)
        self.assertEqual(self.recent(self.customer)[0]['status'],'waiting')
        rider = self.register('partner','rider')
        self.assertEqual([x['id'] for x in self.recent(rider)],[first])
        self.assertEqual(self.act(first,'deliver',rider).status_code,409)
        self.assertEqual(self.act(first,'pickup',rider).status_code,200)
        self.assertEqual(self.act(first,'deliver',rider).status_code,200)
        self.assertEqual([x['status'] for x in self.recent(rider)],['assigned','delivered'])

    def test_rejection_and_scope(self):
        key = self.order()
        other = self.register('owner','second')
        rider = self.register('partner','rider')
        self.assertEqual(self.act(key,'accept',other).status_code,404)
        self.assertEqual(self.act(key,'accept',self.customer).status_code,403)
        self.assertEqual(self.act(key,'reject',self.owner).status_code,200)
        self.assertEqual(self.act(key,'accept',self.owner).status_code,409)
        self.assertEqual(self.recent(rider),[])
        self.assertEqual(self.recent(self.register('customer','bob')),[])

    def test_menu_snapshot_and_auth(self):
        self.order()
        path = f'/api/menu/{self.dish}'
        self.assertEqual(self.http.put(path,headers=self.owner,json={'name':'New dish','paise':6000}).status_code,200)
        self.assertEqual(self.http.delete(path,headers=self.owner).status_code,204)
        self.assertEqual(self.http.get('/api/restaurants').json()[0]['menu'],[])
        self.assertEqual(self.recent(self.customer)[0]['items'][0]['name'],'Poha')
        self.assertEqual(self.http.get('/api/orders').status_code,401)
        self.assertEqual(self.http.post('/api/login',json={'email':'alice@campus.test','password':'demo-test-pass'}).status_code,200)
        self.assertEqual(self.http.post('/api/login',json={'email':'alice@campus.test','password':'wrongpass'}).status_code,401)
