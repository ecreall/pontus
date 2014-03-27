from pontus.testing import FunctionalTests


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

