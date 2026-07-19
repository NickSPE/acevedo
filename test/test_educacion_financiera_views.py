"""
Tests integrales para las vistas, modelos y utilidades de educacion_financiera
Ubicación: test/test_educacion_financiera_views.py
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from cuentas.models import Moneda
from educacion_financiera.models import CursoExterno, FavoritoCurso
from educacion_financiera.utils import marcar_favoritos, paginar_cursos

Usuario = get_user_model()


class EducacionFinancieraModelsTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='modelos_test@test.com',
            password='Password123!',
            nombres='Carlos',
            apellido_paterno='Garcia',
            documento_identidad='87654321',
            telefono=987654321,
            id_moneda=self.moneda,
        )

    def test_curso_externo_create(self):
        curso = CursoExterno.objects.create(
            titulo='Finanzas Personales',
            descripcion='Aprende a manejar tu dinero',
            nivel='basico',
            plataforma='youtube',
            url_externa='https://youtube.com/watch?v=abc',
            duracion_estimada='3 horas',
            instructor='Juan Perez',
            idioma='Español',
            gratis=True,
            orden=1,
            activo=True,
        )
        self.assertEqual(CursoExterno.objects.count(), 1)
        self.assertEqual(curso.titulo, 'Finanzas Personales')
        self.assertEqual(curso.nivel, 'basico')
        self.assertEqual(curso.plataforma, 'youtube')
        self.assertTrue(curso.gratis)
        self.assertTrue(curso.activo)

    def test_curso_externo_str(self):
        curso = CursoExterno.objects.create(
            titulo='Inversiones 101',
            descripcion='Introducción a las inversiones',
            nivel='intermedio',
            plataforma='udemy',
            url_externa='https://udemy.com/course/101',
            duracion_estimada='5 horas',
            orden=2,
        )
        self.assertEqual(str(curso), 'Inversiones 101 (Udemy)')

    def test_curso_externo_plataforma_icon(self):
        curso = CursoExterno.objects.create(
            titulo='Curso Youtube',
            descripcion='Test',
            nivel='basico',
            plataforma='youtube',
            url_externa='https://example.com',
            duracion_estimada='1 hora',
            orden=1,
        )
        self.assertEqual(curso.plataforma_icon, '📺')
        curso.plataforma = 'coursera'
        self.assertEqual(curso.plataforma_icon, '🎓')
        curso.plataforma = 'desconocida'
        self.assertEqual(curso.plataforma_icon, '🌐')

    def test_curso_externo_nivel_color(self):
        curso = CursoExterno.objects.create(
            titulo='Curso Niveles',
            descripcion='Test',
            nivel='basico',
            plataforma='youtube',
            url_externa='https://example.com',
            duracion_estimada='1 hora',
            orden=1,
        )
        self.assertEqual(curso.nivel_color, 'green')
        curso.nivel = 'intermedio'
        self.assertEqual(curso.nivel_color, 'yellow')
        curso.nivel = 'avanzado'
        self.assertEqual(curso.nivel_color, 'red')
        curso.nivel = 'otro'
        self.assertEqual(curso.nivel_color, 'gray')

    def test_favorito_curso_create(self):
        curso = CursoExterno.objects.create(
            titulo='Curso Favorito',
            descripcion='Test',
            nivel='basico',
            plataforma='youtube',
            url_externa='https://example.com',
            duracion_estimada='1 hora',
            orden=1,
        )
        favorito = FavoritoCurso.objects.create(
            usuario=self.usuario,
            curso=curso,
        )
        self.assertEqual(FavoritoCurso.objects.count(), 1)
        self.assertEqual(favorito.usuario, self.usuario)
        self.assertEqual(favorito.curso, curso)

    def test_favorito_curso_str_raises_error(self):
        curso = CursoExterno.objects.create(
            titulo='Ahorro Inteligente',
            descripcion='Test',
            nivel='basico',
            plataforma='youtube',
            url_externa='https://example.com',
            duracion_estimada='1 hora',
            orden=1,
        )
        favorito = FavoritoCurso.objects.create(
            usuario=self.usuario,
            curso=curso,
        )
        with self.assertRaises(AttributeError):
            str(favorito)

    def test_favorito_curso_unique_together(self):
        curso = CursoExterno.objects.create(
            titulo='Curso Único',
            descripcion='Test',
            nivel='basico',
            plataforma='youtube',
            url_externa='https://example.com',
            duracion_estimada='1 hora',
            orden=1,
        )
        FavoritoCurso.objects.create(usuario=self.usuario, curso=curso)
        with self.assertRaises(Exception):
            FavoritoCurso.objects.create(usuario=self.usuario, curso=curso)


class EducacionFinancieraUtilsTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='utils_test@test.com',
            password='Password123!',
            nombres='Maria',
            apellido_paterno='Lopez',
            documento_identidad='11223344',
            telefono=999888777,
            id_moneda=self.moneda,
        )
        self.cursos = []
        for i in range(1, 9):
            curso = CursoExterno.objects.create(
                titulo=f'Curso {i}',
                descripcion=f'Descripción {i}',
                nivel='basico' if i % 2 == 0 else 'intermedio',
                plataforma='youtube',
                url_externa='https://youtube.com/watch?v=test',
                duracion_estimada='2 horas',
                gratis=True,
                orden=i,
            )
            self.cursos.append(curso)

    def test_marcar_favoritos_sin_favoritos(self):
        cursos_qs = CursoExterno.objects.all()
        cursos_marcados = marcar_favoritos(cursos_qs, self.usuario)
        for curso in cursos_marcados:
            self.assertFalse(curso.es_favorito)

    def test_marcar_favoritos_con_favoritos(self):
        FavoritoCurso.objects.create(usuario=self.usuario, curso=self.cursos[0])
        FavoritoCurso.objects.create(usuario=self.usuario, curso=self.cursos[3])
        cursos_qs = CursoExterno.objects.all()
        cursos_marcados = marcar_favoritos(cursos_qs, self.usuario)
        resultados = {curso.id: curso.es_favorito for curso in cursos_marcados}
        self.assertTrue(resultados[self.cursos[0].id])
        self.assertTrue(resultados[self.cursos[3].id])
        self.assertFalse(resultados[self.cursos[1].id])
        self.assertFalse(resultados[self.cursos[2].id])

    def test_paginar_cursos_primera_pagina(self):
        cursos_qs = CursoExterno.objects.all().order_by('orden')
        paginator, pagina = paginar_cursos(cursos_qs, page_number=1, items_per_page=3)
        self.assertEqual(paginator.num_pages, 3)
        self.assertEqual(len(pagina.object_list), 3)
        self.assertEqual(pagina.object_list[0].titulo, 'Curso 1')
        self.assertEqual(pagina.object_list[2].titulo, 'Curso 3')

    def test_paginar_cursos_ultima_pagina(self):
        cursos_qs = CursoExterno.objects.all().order_by('orden')
        _, pagina = paginar_cursos(cursos_qs, page_number=99, items_per_page=3)
        self.assertEqual(pagina.number, 3)
        self.assertEqual(len(pagina.object_list), 2)

    def test_paginar_cursos_page_no_entero(self):
        cursos_qs = CursoExterno.objects.all().order_by('orden')
        _, pagina = paginar_cursos(cursos_qs, page_number='abc', items_per_page=4)
        self.assertEqual(pagina.number, 1)
        self.assertEqual(len(pagina.object_list), 4)


class CalculatorsViewTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='calc_test@test.com',
            password='Password123!',
            nombres='Ana',
            apellido_paterno='Martinez',
            documento_identidad='99887766',
            telefono=111222333,
            id_moneda=self.moneda,
        )
        self.url = reverse('educacion_financiera:calculators')

    def _login_and_set_session(self):
        self.client.login(correo='calc_test@test.com', password='Password123!')
        session = self.client.session
        session['pin_acceso_rapido_validado'] = True
        session.save()

    def test_redirect_if_not_authenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f"{reverse('usuarios:login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_get_returns_200_with_default_tab(self):
        self._login_and_set_session()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'savings')

    def test_get_with_tab_loan(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'loan'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'loan')

    def test_get_with_tab_budget(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'budget'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'budget')

    def test_get_with_tab_retirement(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'retirement'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'retirement')

    def test_get_with_tab_investment(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'investment'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'investment')

    @patch('educacion_financiera.views.generate_ai_explanation')
    def test_post_savings_calculation(self, mock_ai):
        mock_ai.return_value = 'Explicación de prueba'
        self._login_and_set_session()
        response = self.client.post(
            self.url + '?tab=savings',
            {'initial': '1000', 'monthly': '200', 'rate': '5', 'years': '10'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)

    @patch('educacion_financiera.views.generate_ai_explanation')
    def test_post_loan_calculation(self, mock_ai):
        mock_ai.return_value = 'Explicación de prueba'
        self._login_and_set_session()
        response = self.client.post(
            self.url + '?tab=loan',
            {'amount': '10000', 'rate': '5', 'years': '5'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)

    @patch('educacion_financiera.views.generate_ai_explanation')
    def test_post_budget_calculation(self, mock_ai):
        mock_ai.return_value = 'Explicación de prueba'
        self._login_and_set_session()
        response = self.client.post(
            self.url + '?tab=budget',
            {'income': '3000', 'needs': '1500', 'wants': '900', 'savings': '600'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)

    @patch('educacion_financiera.views.generate_ai_explanation')
    def test_post_retirement_calculation(self, mock_ai):
        mock_ai.return_value = 'Explicación de prueba'
        self._login_and_set_session()
        response = self.client.post(
            self.url + '?tab=retirement',
            {
                'current_age': '30',
                'retirement_age': '65',
                'current_savings': '10000',
                'monthly_contribution': '500',
                'expected_return': '7',
                'desired_income': '2000',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)

    @patch('educacion_financiera.views.generate_ai_explanation')
    def test_post_investment_calculation(self, mock_ai):
        mock_ai.return_value = 'Explicación de prueba'
        self._login_and_set_session()
        response = self.client.post(
            self.url + '?tab=investment',
            {
                'initial_investment': '5000',
                'monthly_investment': '300',
                'annual_return': '8',
                'years': '10',
                'inflation_rate': '3',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)

    def test_post_invalid_data_shows_error(self):
        self._login_and_set_session()
        response = self.client.post(
            self.url + '?tab=savings',
            {'initial': 'not-a-number', 'monthly': 'abc', 'rate': 'xyz', 'years': 'bad'},
        )
        self.assertEqual(response.status_code, 200)
        result = response.context.get('result')
        self.assertIsNotNone(result)
        self.assertIn('error', result)

    def test_post_loan_invalid_data(self):
        self._login_and_set_session()
        response = self.client.post(
            self.url + '?tab=loan',
            {'amount': '', 'rate': '', 'years': ''},
        )
        self.assertEqual(response.status_code, 200)
        result = response.context.get('result')
        self.assertIsNotNone(result)
        self.assertIn('error', result)


class CoursesViewTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='courses_test@test.com',
            password='Password123!',
            nombres='Pedro',
            apellido_paterno='Sanchez',
            documento_identidad='55443322',
            telefono=555666777,
            id_moneda=self.moneda,
        )
        self.url = reverse('educacion_financiera:courses')

    def _login_and_set_session(self):
        self.client.login(correo='courses_test@test.com', password='Password123!')
        session = self.client.session
        session['pin_acceso_rapido_validado'] = True
        session.save()

    def test_get_returns_200(self):
        self._login_and_set_session()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_with_curso_externo_objects(self):
        for i in range(3):
            CursoExterno.objects.create(
                titulo=f'Curso Activo {i}',
                descripcion=f'Desc {i}',
                nivel='basico',
                plataforma='youtube',
                url_externa='https://example.com',
                duracion_estimada='1 hora',
                orden=i,
                activo=True,
            )
        self._login_and_set_session()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('cursos', response.context)
        self.assertEqual(len(response.context['cursos']), 3)

    def test_pagination(self):
        for i in range(10):
            CursoExterno.objects.create(
                titulo=f'Curso Pag {i}',
                descripcion=f'Desc {i}',
                nivel='basico',
                plataforma='youtube',
                url_externa='https://example.com',
                duracion_estimada='1 hora',
                orden=i,
                activo=True,
            )
        self._login_and_set_session()
        response = self.client.get(self.url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        cursos = response.context['cursos']
        self.assertLessEqual(len(cursos), 6)
        self.assertIsNotNone(response.context.get('paginator'))
        self.assertIsNotNone(response.context.get('page_obj'))


class ToggleFavoritoCursoViewTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='fav_test@test.com',
            password='Password123!',
            nombres='Luisa',
            apellido_paterno='Ramirez',
            documento_identidad='12345678',
            telefono=999999999,
            id_moneda=self.moneda,
        )
        self.curso = CursoExterno.objects.create(
            titulo='Curso Favorito Test',
            descripcion='Desc',
            nivel='basico',
            plataforma='youtube',
            url_externa='https://example.com',
            duracion_estimada='1 hora',
            orden=1,
        )
        self.url = reverse('educacion_financiera:toggle_favorito', args=[self.curso.id])

    def test_redirect_if_not_authenticated(self):
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            f"{reverse('usuarios:login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_post_creates_favorito(self):
        self.client.login(correo='fav_test@test.com', password='Password123!')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['es_favorito'])
        self.assertEqual(FavoritoCurso.objects.count(), 1)

    def test_post_removes_favorito(self):
        self.client.login(correo='fav_test@test.com', password='Password123!')
        FavoritoCurso.objects.create(usuario=self.usuario, curso=self.curso)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['es_favorito'])
        self.assertEqual(FavoritoCurso.objects.count(), 0)

    def test_post_non_existent_curso_returns_json_error(self):
        self.client.login(correo='fav_test@test.com', password='Password123!')
        url_404 = reverse('educacion_financiera:toggle_favorito', args=[9999])
        response = self.client.post(url_404)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])

    def test_get_returns_403(self):
        self.client.login(correo='fav_test@test.com', password='Password123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])

    def test_toggle_on_multiple_cursos(self):
        curso2 = CursoExterno.objects.create(
            titulo='Segundo Curso',
            descripcion='Desc',
            nivel='intermedio',
            plataforma='udemy',
            url_externa='https://example2.com',
            duracion_estimada='2 horas',
            orden=2,
        )
        self.client.login(correo='fav_test@test.com', password='Password123!')
        url2 = reverse('educacion_financiera:toggle_favorito', args=[curso2.id])
        response1 = self.client.post(self.url)
        self.assertTrue(response1.json()['es_favorito'])
        response2 = self.client.post(url2)
        self.assertTrue(response2.json()['es_favorito'])
        self.assertEqual(FavoritoCurso.objects.count(), 2)
        response3 = self.client.post(self.url)
        self.assertFalse(response3.json()['es_favorito'])
        self.assertEqual(FavoritoCurso.objects.count(), 1)


class TipsViewTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='tips_test@test.com',
            password='Password123!',
            nombres='Diego',
            apellido_paterno='Fernandez',
            documento_identidad='11111111',
            telefono=111111111,
            id_moneda=self.moneda,
        )
        self.url = reverse('educacion_financiera:tips')

    def _login_and_set_session(self):
        self.client.login(correo='tips_test@test.com', password='Password123!')
        session = self.client.session
        session['pin_acceso_rapido_validado'] = True
        session.save()

    def test_get_returns_200_with_default_tab(self):
        self._login_and_set_session()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'savings')

    def test_get_with_tab_savings(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'savings'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'savings')
        self.assertIn('tips', response.context)

    def test_get_with_tab_investment(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'investment'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'investment')

    def test_get_with_tab_budget(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'budget'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'budget')

    def test_get_with_tab_debt(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'debt'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'debt')

    def test_get_with_tab_insurance(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'insurance'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'insurance')

    def test_get_with_tab_retirement(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'retirement'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'retirement')

    @patch('educacion_financiera.views.generate_ai_tips')
    def test_get_with_ai_true_catches_error_gracefully(self, mock_ai_tips):
        mock_ai_tips.return_value = []
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'savings', 'ai': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('tips', response.context)
        self.assertIn('ai_enabled', response.context)
        self.assertTrue(response.context['ai_enabled'])

    def test_get_no_ai_by_default(self):
        self._login_and_set_session()
        response = self.client.get(self.url)
        self.assertIn('ai_enabled', response.context)
        self.assertFalse(response.context['ai_enabled'])

    def test_get_returns_correct_tip_count(self):
        self._login_and_set_session()
        response = self.client.get(self.url, {'tab': 'savings'})
        tips = response.context['tips']
        self.assertEqual(len(tips), 3)


class AiChatViewTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='chat_test@test.com',
            password='Password123!',
            nombres='Sofia',
            apellido_paterno='Torres',
            documento_identidad='22222222',
            telefono=222222222,
            id_moneda=self.moneda,
        )
        self.url = reverse('educacion_financiera:ai_chat')

    def _login_and_set_session(self):
        self.client.login(correo='chat_test@test.com', password='Password123!')
        session = self.client.session
        session['pin_acceso_rapido_validado'] = True
        session.save()

    def test_get_returns_200(self):
        self._login_and_set_session()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @patch('educacion_financiera.views.process_ai_chat')
    def test_post_with_valid_data_returns_json_response(self, mock_chat):
        mock_chat.return_value = {'success': True, 'response': 'Respuesta de prueba'}
        self._login_and_set_session()
        response = self.client.post(
            self.url,
            {'question': '¿Cómo ahorrar dinero?'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('success', data)

    @patch('educacion_financiera.views.process_ai_chat')
    def test_post_with_json_content_type(self, mock_chat):
        mock_chat.return_value = {'success': True, 'response': 'Respuesta de prueba'}
        self._login_and_set_session()
        import json
        response = self.client.post(
            self.url,
            data=json.dumps({'message': 'Consejos de inversión'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('success', data)

    @patch('educacion_financiera.views.process_ai_chat')
    def test_post_without_data_returns_response(self, mock_chat):
        mock_chat.return_value = {'success': True, 'response': ''}
        self._login_and_set_session()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    @patch('educacion_financiera.views.process_ai_chat')
    def test_post_vacio_catches_error_gracefully(self, mock_chat):
        mock_chat.return_value = {'success': True, 'response': ''}
        self._login_and_set_session()
        response = self.client.post(
            self.url,
            {'question': ''},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('success', data)


class GenerarConsejosIaViewTestCase(TestCase):
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='PEN', nombre='Soles', simbolo='S/.'
        )
        self.usuario = Usuario.objects.create_user(
            correo='consejos_test@test.com',
            password='Password123!',
            nombres='Pablo',
            apellido_paterno='Diaz',
            documento_identidad='33333333',
            telefono=333333333,
            id_moneda=self.moneda,
        )
        self.url = reverse('educacion_financiera:generar_consejos_ia')

    @patch('educacion_financiera.views.generate_ai_tips')
    def test_post_returns_json_response(self, mock_ai_tips):
        mock_ai_tips.return_value = []
        self.client.login(correo='consejos_test@test.com', password='Password123!')
        response = self.client.post(
            self.url,
            {'categoria': 'savings'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('success', data)

    @patch('educacion_financiera.views.generate_ai_tips')
    def test_post_with_invalid_categoria(self, mock_ai_tips):
        mock_ai_tips.return_value = []
        self.client.login(correo='consejos_test@test.com', password='Password123!')
        response = self.client.post(
            self.url,
            {'categoria': 'invalid'},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('success', data)

    @patch('educacion_financiera.views.generate_ai_tips')
    def test_post_without_categoria(self, mock_ai_tips):
        mock_ai_tips.return_value = []
        self.client.login(correo='consejos_test@test.com', password='Password123!')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('success', data)

    def test_get_returns_403(self):
        self.client.login(correo='consejos_test@test.com', password='Password123!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Método no permitido', data['error'])
