from pontus.testing import FunctionalTests

from pontus.tests.example.app import ViewA, BehaviorA, MultipleViewA, ViewB, BehaviorB

class TestRelationsCatalog(FunctionalTests):

    def test_login(self):

        res = self.testapp.get('/manage')
        res.form['login'] = 'admin'
        res.form['password'] = 'admin'
        res = res.form.submit('form.submitted')
        self.assertEqual(res.status_int, 302)

        res = res.follow()
        res = res.follow()
        res.mustcontain('Log Out')

    def test_BasicView(self):
        self.request.validationA = True
        self.request.viewexecuted = []
        view = ViewA(None, self.request)
        result = view()
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(view.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][view.coordinates]), 1)

        item = result['coordinates'][view.coordinates][0]
        self.assertIn('body', item)
        self.assertIn('view', item)
        self.assertIn('id', item)
        self.assertIn('isactive', item)
        self.assertEqual(item['body'], "Hello_"+view.title+"\n")
        self.assertEqual(item['view'], view)
        self.assertEqual(item['id'], view.viewid)
        self.assertEqual(item['isactive'], True)
        self.assertIn('behaviorA',self.request.viewexecuted)

        self.request.validationA = False
        self.request.viewexecuted = []
        view = ViewA(None, self.request)
        result = view()
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(view.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][view.coordinates]), 1)

        item = result['coordinates'][view.coordinates][0]
        self.assertIn('messages', item)
        self.assertEqual(len(item['messages']), 1)
        self.assertIn('body', item)
        self.assertIn('view', item)
        self.assertIn('id', item)
        self.assertIn('isactive', item)
        self.assertEqual(item['body'], "")
        self.assertEqual(item['view'], view)
        self.assertEqual(item['id'], view.viewid)
        self.assertEqual(item['isactive'], True)
        self.assertEqual(len(self.request.viewexecuted), 0)
        self.assertIn('danger', item['messages'])


    def test_MultipleView(self):
        self.request.validationA = True
        self.request.validationB = True
        self.request.viewexecuted = []
        view = MultipleViewA(None, self.request)
        result = view()
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(ViewA.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][ViewA.coordinates]),1)

        items_body = [item['body'] for item in  result['coordinates'][ViewA.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("Hello_"+ViewA.title+"\n")>-1), True )
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n")>-1), True )
        self.assertEqual(len(self.request.viewexecuted), 2)
        self.assertIn('behaviorA',self.request.viewexecuted)
        self.assertIn('behaviorB',self.request.viewexecuted)

        self.request.validationA = False
        self.request.viewexecuted = []
        view = MultipleViewA(None, self.request)
        result = view()
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(ViewA.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][ViewA.coordinates]),1)

        items_body = [item['body'] for item in  result['coordinates'][ViewA.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("Hello_"+ViewA.title+"\n")>-1), False )
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n")>-1), True )
        self.assertEqual(len(self.request.viewexecuted), 1)
        self.assertIn('behaviorB',self.request.viewexecuted)

        self.request.validationA = False
        self.request.validationB = False
        self.request.viewexecuted = []
        view = MultipleViewA(None, self.request)
        result = view()
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(view.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][view.coordinates]),1)
        item = result['coordinates'][view.coordinates][0]
        self.assertIn('messages', item)
        self.assertEqual(len(item['messages']), 1)

        items_body = [item['body'] for item in  result['coordinates'][view.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("Hello_"+ViewA.title+"\n")>-1), False )
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n")>-1), False )
        self.assertEqual(len(self.request.viewexecuted), 0)
