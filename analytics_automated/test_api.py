import json
import io
from unipath import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from .api import SubmissionDetails
from .models import *
from .model_factories import *
from .tasks import *


class JobListTests(APITestCase):

    def test_return_of_available_job_types(self):
        j1 = JobFactory.create(name="job1")
        j2 = JobFactory.create(name="job2")
        response = self.client.get(reverse('job',)+".json")
        response.render()
        self.assertEqual(response.status_code, 200)
        test_data = '{"count":2,"next":null,"previous":null,' \
                    '"results":[{"pk":1,"name":"job1"},{"pk":2,"name":"job2"}]}'
        self.assertEqual(response.content.decode("utf-8"), test_data)

        def tearDown(self):
            Backend.objects.all().delete()
            Job.objects.all().delete()
            Task.objects.all().delete()
            Step.objects.all().delete()
            Submission.objects.all().delete()
            Parameter.objects.all().delete()
            Result.objects.all().delete()


class SubmissionDetailTests(APITestCase):

    file = ''
    data = {}
    factory = APIRequestFactory()
    t = None
    b = None

    def setUp(self):
        self.file = SimpleUploadedFile('file1.txt',
                                       bytes('these are the file contents!',
                                             'utf-8'))
        self.data = {'input_data': self.file,
                     'job': 'job1',
                     'submission_name': 'test',
                     'email': 'a@b.com'}
        j1 = JobFactory.create(name="job1")
        self.b = BackendFactory.create(root_path="/tmp/")
        self.t = TaskFactory.create(backend=self.b, name="task1", executable="ls")
        s = StepFactory(job=j1, task=self.t, ordering=0)

    def tearDown(self):
        Backend.objects.all().delete()
        Job.objects.all().delete()
        Task.objects.all().delete()
        Step.objects.all().delete()
        Submission.objects.all().delete()
        Parameter.objects.all().delete()
        Result.objects.all().delete()

    def test_submission_detail_is_returned(self,):
        s1 = SubmissionFactory.create()
        response = self.client.get(reverse('submissionDetail',
                                           args=[s1.UUID, ]) + ".json")
        self.assertEqual(response.status_code, 200)
        test_data = '{{"submission_name":"submission_1","UUID":"{0}"' \
                    ',"state":"Submitted","results":[]}}'.format(s1.UUID)
        self.assertEqual(response.content.decode("utf-8"), test_data)

    def test_submission_with_results_is_returned(self,):
        s1 = SubmissionFactory.create()
        t1 = TaskFactory.create(name='task1')
        r1 = ResultFactory.create(submission=s1,
                                  task=t1,
                                  name='test',
                                  message='a result',
                                  step=1,
                                  result_data=self.file,)
        response = self.client.get(reverse('submissionDetail',
                                           args=[s1.UUID, ]) + ".json")
        self.assertEqual(response.status_code, 200)
        test_data = '{{"submission_name":"{0}","UUID":"{1}"' \
                    ',"state":"Submitted","results":[{{"task":{2},' \
                    '"name":"{3}","message":"{4}","step":{5},' \
                    '"result_data":"{6}"}}]}}'.format(s1.submission_name,
                                                      s1.UUID, t1.pk, 'test',
                                                      r1.message, r1.step,
                                                      "http://testserver" +
                                                      r1.result_data.url)
        self.assertEqual(response.content.decode("utf-8"), test_data)

    @patch('builtins.eval', return_value=True)
    def test_submission_accepts_when_all_params_given(self, m):
        p1 = ParameterFactory.create(task=self.t, rest_alias="this")
        p2 = ParameterFactory.create(task=self.t, rest_alias="that")
        self.data['task1_this'] = "Value1"
        self.data['task1_that'] = "Value2"
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('builtins.eval', return_value=True)
    def test_submission_rejects_when_a_param_is_missed(self, m):
        p1 = ParameterFactory.create(task=self.t, rest_alias="this")
        p2 = ParameterFactory.create(task=self.t, rest_alias="that")
        self.data['task1_this'] = "Value1"
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    @patch('builtins.eval', return_value=True)
    def test_submission_ignores_undefined_params(self, m):
        p1 = ParameterFactory.create(task=self.t, rest_alias="this")
        self.data['task1_strange'] = "Value2"
        self.data['task1_this'] = "Value1"
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('builtins.eval', return_value=True)
    def test_submission_checks_params_across_more_than_one_task(self, m):
        p1 = ParameterFactory.create(task=self.t, rest_alias="this")
        t2 = TaskFactory.create(backend=self.b, name="task2", executable="ls")
        p2 = ParameterFactory.create(task=t2, rest_alias="this2")
        self.data['task2_this2'] = "Value2"
        self.data['task1_this'] = "Value1"
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('builtins.eval', return_value=True)
    def test_valid_submission_post_creates_entry(self, m):
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rejection_with_bad_email(self):
        self.data['email'] = 'b'
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejection_with_bad_job_id(self):
        self.data['job'] = 'job34'
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_rejection_with_blank_submission_name(self):
        self.data['submission_name'] = ""
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejection_without_submission_name(self):
        del(self.data['submission_name'])
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejection_without_email(self):
        del(self.data['email'])
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejection_without_job(self):
        del(self.data['job'])
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejection_without_input_data(self):
        del(self.data['input_data'])
        request = self.factory.post(reverse('submission'), self.data,
                                    format='multipart')
        view = SubmissionDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
