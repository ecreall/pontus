# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi
from pontus.testing import FunctionalTests

from pontus.tests.example.app import (
    ViewA, MultipleViewA, ViewB,
    MultipleFromViewA, FormViewA, objectA, objectB)


class TestPontusView(FunctionalTests):

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

    #def test_boucle_simple(self): # Moyenne de 0,18 ms par calcule de vue
    #    for x in range(100000):
    #        self.test_BasicView()


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
        self.assertEqual(len(result['coordinates'][ViewA.coordinates]), 1)

        items_body = [item['body']
                for item in result['coordinates'][ViewA.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("Hello_"+ViewA.title+"\n") > -1), False)
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n") > -1), True)
        self.assertEqual(len(self.request.viewexecuted), 1)
        self.assertIn('behaviorB', self.request.viewexecuted)

        self.request.validationA = False
        self.request.validationB = False
        self.request.viewexecuted = []
        view = MultipleViewA(None, self.request)
        result = view()
        self.assertEqual(isinstance(result, dict), True)
        self.assertIn('coordinates', result)
        self.assertIn(view.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][view.coordinates]), 1)
        item = result['coordinates'][view.coordinates][0]
        self.assertIn('messages', item)
        self.assertEqual(len(item['messages']), 1)

        items_body = [item['body'] for item in  result['coordinates'][view.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("Hello_"+ViewA.title+"\n") > -1), False)
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n") > -1), False)
        self.assertEqual(len(self.request.viewexecuted), 0)

    def test_MultipleFormView(self, log=0):
        self.request.validationA = True
        self.request.validationB = True
        self.request.viewexecuted = []
        view = MultipleFromViewA(None, self.request)
        result = view()
        self.assertTrue(view.isexecutable)
        self.assertTrue(isinstance(result, dict))
        self.assertIn('coordinates', result)
        self.assertIn(ViewA.coordinates, result['coordinates'])
        self.assertEqual(len(result['coordinates'][ViewA.coordinates]), 1)

        items_body = [item['body'] for item in result['coordinates'][FormViewA.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertTrue(items_body[0].find("title") > -1)
        self.assertTrue(items_body[0].find("Hello_"+ViewB.title+"\n") > -1)
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

        items_body = [item['body'] for item in result['coordinates'][ViewB.coordinates]]
        self.assertEqual(len(items_body), 1)
        self.assertEqual((items_body[0].find("Title")>-1), False )
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
        self.assertEqual((items_body[0].find("title")>-1), False)
        self.assertEqual((items_body[0].find("Hello_"+ViewB.title+"\n")>-1), False )
        self.assertEqual(len(self.request.viewexecuted), 0)

        runtime = self.app['runtime']
        if log==0:
            self.test_login()
        self.assertEqual(runtime.title, 'Runtime')
        res = self.testapp.get('/runtime/@@multipleformviewa')
        self.assertEqual((str(res.html).find("title") > -1), True)
        self.assertEqual((str(res.html).find("Hello_"+ViewB.title+"\n") > -1), True)
        res.form['title'] = 'newtitleA'
        res = res.form.submit('Behavior_A')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(runtime.title, 'newtitleA')

        res = self.testapp.get('/runtime/@@multipleformviewa')
        self.assertEqual((str(res.html).find("title")>-1), True)
        self.assertEqual((str(res.html).find("Hello_"+ViewB.title+"\n") > -1), True)
        res.form['title'] = ''
        res = res.form.submit('Behavior_A')
        self.assertEqual(res.status_int, 200)
        self.assertEqual((str(res.html).find("title") > -1), True)
        self.assertEqual((str(res.html).find("Hello_"+ViewB.title+"\n") > -1), True)
        res.form['title'] = 'Runtime'
        res = res.form.submit('Behavior_A')
        self.assertEqual(runtime.title, 'Runtime')

    #def test_boocle_multiform(self): # Moyenne de 45 ms par calcule de vue
    #    for x in range(1000):
    #        self.test_MultipleFormView(log=x) 

    def test_MergedFormsView(self):
        self.request.validationA = True
        self.request.validationB = True
        self.request.viewexecuted = []
        self.app['objecta'] = objectA
        self.app['objectb'] = objectB
        self.test_login()
        res = self.testapp.get('/runtime/@@mergedformsviewa')
        titles = [f for f in res.form.fields['title']
                  if f.__class__.__name__ == 'Text']
        self.assertEqual(len(titles), 2 )
        forms = set(res.forms.values())
        self.assertEqual(len(forms), 1 )
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
        res = self.testapp.get('/runtime/@@mergedformsviewa')
        titles = [f for f in res.form.fields['title']
                  if f.__class__.__name__ == 'Text']
        self.assertEqual(len(titles), 1)
        forms = set(res.forms.values())
        self.assertEqual(len(forms), 1)
        title_values = [t.value for t in titles]
        self.assertIn('newtitleb', title_values)
        for field in res.form.fields['title']:
            if field.value == 'newtitleb':
                field.value__set('objectb')

        res = res.form.submit('Behavior_A_All')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(objectA.title, 'notnewtitlea')
        self.assertEqual(objectB.title, 'objectb')

        objectB.title = 'notnewtitlea'
        res = self.testapp.get('/runtime/@@mergedformsviewa')
        self.assertEqual(res.status_int, 200)
        forms = set(res.forms.values())
        self.assertEqual(len(forms), 0)

    def test_omitedfield(self):
        self.test_login()
        runtime = self.app['runtime']
        res = self.testapp.get('/runtime/@@formviewb')
        titles = [f for f in res.form.fields['title']
                  if f.__class__.__name__ == 'Text']
        descriptions = [f for f in res.form.fields['description']
                  if f.__class__.__name__ == 'Text']
        self.assertEqual(len(titles), 1 )
        self.assertEqual(len(descriptions), 1 )
        forms = set(res.forms.values())
        self.assertEqual(len(forms), 1 )
        title_values = [t.value for t in titles]
        old_titles = runtime.title
        self.assertIn(runtime.title, title_values)
        description_values = [t.value for t in descriptions]
        self.assertIn('', description_values)
        res.form.fields['title'][0].value__set('newtitleruntime')
        res.form.fields['description'][0].value__set('newdescriptionruntime')
        res = res.form.submit('Behavior_C')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(runtime.title, old_titles) # title is omited
        self.assertEqual(runtime.description, 'newdescriptionruntime')

    def test_omitedfield_SubList(self):
        self.test_login()
        pdc = self.app['process_definition_container']
        res = self.testapp.get('/process_definition_container/@@formviewc')
        titles = [f for f in res.form.fields['title']
                  if f.__class__.__name__ == 'Text']
        descriptions = [f for f in res.form.fields['description']
                  if f.__class__.__name__ == 'Text']
        total = len(pdc.definitions)+1
        self.assertEqual(len(titles), total )
        self.assertEqual(len(descriptions), total )
        title_values = [t.value for t in titles]
        self.assertIn(pdc.title, title_values)
        description_values = [t.value for t in descriptions]
        self.assertIn(pdc.description, description_values)
        for defi in pdc.definitions:
            self.assertIn(defi.title, title_values)
            self.assertIn(defi.description, description_values)

        res.form.fields['title'][0].value__set('newtitledescription')
        res.form.fields['description'][0].value__set('newdescriptiondescription')
        i = 0
        for field in res.form.fields['description'][1:]:
            field.value__set('newdescription'+str(i))
            i = i+1

        i = 0
        for field in res.form.fields['title'][1:]:
            field.value__set('newtitle'+str(i)) # set titles
            i = i+1

        res = res.form.submit('Behavior_C')
        self.assertEqual(res.status_int, 302)
        self.assertEqual(pdc.title, 'newtitledescription')
        self.assertEqual(pdc.description, 'newdescriptiondescription')
        for defi in pdc.definitions:
            self.assertFalse(defi.title.startswith('newtitle'))  # title is omited
            self.assertTrue(defi.description.startswith('newdescription'))
