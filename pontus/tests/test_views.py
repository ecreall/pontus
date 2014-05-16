from pontus.testing import FunctionalTests

from pontus.tests.example.app import ViewA, BehaviorA, MultipleViewA, ViewB, BehaviorB, MultipleFromViewA, FormViewA, MergedFormsViewA, objectA, objectB
from dace.objectofcollaboration.object import Object

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

    def test_MultipleFormView(self):
        self.request.validationA = True
        self.request.validationB = True
        self.request.viewexecuted = []
        view = MultipleFromViewA(None, self.request)
        result = view()
        self.assertEqual(view.isexecutable, True)
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(ViewA.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][ViewA.coordinates]),1)

        items_body = [item['body'] for item in  result['coordinates'][FormViewA.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("title")>-1), True )
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n")>-1), True )
        self.assertEqual(len(self.request.viewexecuted), 1)
        self.assertIn('behaviorB',self.request.viewexecuted)

        self.request.validationA = False
        self.request.viewexecuted = []
        view = MultipleFromViewA(None, self.request)
        result = view()
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(ViewB.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][ViewB.coordinates]),1)

        items_body = [item['body'] for item in  result['coordinates'][ViewB.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("title")>-1), False )
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n")>-1), True )
        self.assertEqual(len(self.request.viewexecuted), 1)
        self.assertIn('behaviorB',self.request.viewexecuted)

        self.request.validationA = False
        self.request.validationB = False
        self.request.viewexecuted = []
        view = MultipleFromViewA(None, self.request)
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
        self.assertEqual((items_body[0].find("title")>-1), False )
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n")>-1), False )
        self.assertEqual(len(self.request.viewexecuted), 0)

        runtime = self.app['runtime']
        self.test_login()
        self.assertEqual(runtime.title, 'Runtime')
        res = self.testapp.get('/manage/runtime/@@multipleformviewa')
        self.assertEqual((str(res.html).find("title")>-1), True )
        self.assertEqual((str(res.html).find("Hello_"+ViewB.title+"\n")>-1), True )
        res.form['title'] = 'newtitleA'
        res = res.form.submit('Behavior_A')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(runtime.title, 'newtitleA')

        res = self.testapp.get('/manage/runtime/@@multipleformviewa')
        self.assertEqual((str(res.html).find("title")>-1), True )
        self.assertEqual((str(res.html).find("Hello_"+ViewB.title+"\n")>-1), True )
        res.form['title'] = ''
        res = res.form.submit('Behavior_A')
        self.assertEqual(res.status_int, 200)
        self.assertEqual((str(res.html).find("title")>-1), True )
        self.assertEqual((str(res.html).find("Hello_"+ViewB.title+"\n")>-1), True )
        res.form['title'] = 'Runtime'
        res = res.form.submit('Behavior_A')
        self.assertEqual(runtime.title, 'Runtime')

    def test_MergedFormsView(self):
        self.request.validationA = True
        self.request.validationB = True
        self.request.viewexecuted = []
        self.app['objecta'] = objectA
        self.app['objectb'] = objectB
        self.test_login()
        res = self.testapp.get('/manage/runtime/@@mergedformsviewa')
        titles = [f for f in res.form.fields['title'] if f.__class__.__name__ == 'Text']
        self.assertEqual(len(titles), 2 )
        title_values = [t.value for t in titles]
        self.assertIn('objecta', title_values)
        self.assertIn('objectb', title_values)
        for field in res.form.fields['title']:
            if field.value == 'objecta':
                field.value__set('newtitlea')

            if field.value == 'objectb':
                field.value__set('newtitleb')

        res = res.form.submit('Behavior_A_All')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(objectA.title, 'newtitlea')
        self.assertEqual(objectB.title, 'newtitleb')

        objectA.title = 'notnewtitlea'
        res = self.testapp.get('/manage/runtime/@@mergedformsviewa')
        titles = [f for f in res.form.fields['title'] if f.__class__.__name__ == 'Text']
        self.assertEqual(len(titles), 1 )
        title_values = [t.value for t in titles]
        self.assertIn('newtitleb', title_values)
        for field in res.form.fields['title']:
            if field.value == 'newtitleb':
                field.value__set('objectb')

        res = res.form.submit('Behavior_A_All')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(objectA.title, 'notnewtitlea')
        self.assertEqual(objectB.title, 'objectb')

        objectB.title = 'notobjectb'
        res = self.testapp.get('/manage/runtime/@@mergedformsviewa')
        titles = [f for f in res.form.fields['title'] if f.__class__.__name__ == 'Text']
        self.assertEqual(len(titles), 1 )
        title_values = [t.value for t in titles]
        self.assertIn('newtitleb', title_values)
        for field in res.form.fields['title']:
            if field.value == 'newtitleb':
                field.value__set('objectb')

        res = res.form.submit('Behavior_A_All')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(objectA.title, 'notnewtitlea')
        self.assertEqual(objectB.title, 'objectb')


