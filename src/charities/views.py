import copy
from rest_framework import status, generics
from rest_framework.decorators import permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

# import modules from app
from accounts.permissions import IsCharityOwner, IsBenefactor
from charities.models import Task, Benefactor, Charity
from charities.serializers import (
    TaskSerializer, CharitySerializer, BenefactorSerializer
)

# Benefactor Class
class BenefactorRegistration(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BenefactorSerializer
    queryset = Benefactor.objects.all()

    # saving new benefactor
    def post(self, request, *args, **kwargs):
        data = copy.deepcopy(request.data)
        data.update({"user":request.user.pk})
        temp = self.serializer_class(data = data)
        if temp.is_valid():
            temp.save()
            return Response(temp.data, status = status.HTTP_201_CREATED)
        else:
            return Response(temp.errors, status = status.HTTP_404_NOT_FOUND)


# charity class
class CharityRegistration(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CharitySerializer
    queryset = Charity.objects.all()

    # saving new charity
    def post(self, request, *args, **kwargs):
        data = copy.deepcopy(request.data)
        data.update({"user":request.user.pk})
        temp = self.serializer_class(data = data)
        if temp.is_valid():
            temp.save()
            return Response(temp.data, status = status.HTTP_201_CREATED)
        else:
            return Response(temp.errors, status = status.HTTP_404_NOT_FOUND)


# task class
class Tasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    #get all related tasks -> look in models
    def get_queryset(self):
        return Task.objects.all_related_tasks_to_user(self.request.user)

    #saving new task
    def post(self, request, *args, **kwargs):
        data = {
            **request.data,
            "charity_id": request.user.charity.id
        }
        serializer = self.serializer_class(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = [IsCharityOwner, ]

        return [permission() for permission in self.permission_classes]

    def filter_queryset(self, queryset):
        filter_lookups = {}
        for name, value in Task.filtering_lookups:
            param = self.request.GET.get(value)
            if param:
                filter_lookups[name] = param
        exclude_lookups = {}
        for name, value in Task.excluding_lookups:
            param = self.request.GET.get(value)
            if param:
                exclude_lookups[name] = param

        return queryset.filter(**filter_lookups).exclude(**exclude_lookups)


# request tasks for benefactor
class TaskRequest(APIView):

    permission_classes = [IsAuthenticated, IsBenefactor, ]
    queryset = Task.objects.all()

    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        if task.state == 'P':
            # look in models for more information about this method
            task.assign_to_benefactor(request.user.benefactor)
            return Response(data={'detail': 'Request sent.'}, status=status.HTTP_200_OK)
        else:
            return Response(data={'detail': 'This task is not pending.'}, status=status.HTTP_404_NOT_FOUND)


# response to tasks from charities
class TaskResponse(APIView):
    permission_classes = (IsAuthenticated, IsCharityOwner, )
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def post(self, request, task_id, **kwargs):
        task = get_object_or_404(Task, id=task_id)
        data = request.data["response"]
        # for waiting tasks
        if task.state == 'W':
            # for assigned task
            if data == 'A':
                # for more information about this method look inside models.
                task.response_to_benefactor_request(response='A')
                return Response(data={'detail': 'Response sent.'}, status=status.HTTP_200_OK)
            # for requested tasks
            if data == 'R':
                task.response_to_benefactor_request(response='R')
                return Response(data={'detail': 'Response sent.'}, status=status.HTTP_200_OK)
        if task.state != 'W':
            # for done tasks
            if data == 'D':
                return Response(data={'detail': 'Required field ("A" for accepted / "R" for rejected)'},
                            status=status.HTTP_400_BAD_REQUEST)
            return Response(data={'detail': 'This task is not waiting.'}, status=status.HTTP_404_NOT_FOUND)


class DoneTask(APIView):
    permission_classes = (IsAuthenticated, IsCharityOwner, )
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    # validating done tasks from charity
    def post(self, request, task_id, **kwargs):
        task = get_object_or_404(Task, id=task_id)
        if task.state != 'A':
            return Response(data={'detail': 'Task is not assigned yet.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            task.done()
            return Response(data={'detail': 'Task has been done successfully.'}, status=status.HTTP_200_OK)
