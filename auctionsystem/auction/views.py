from atexit import register
from cgi import print_environ_usage
from multiprocessing import current_process
import time
from unicodedata import category
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.utils import timezone
from .mixins import *
from .models import *
from django.contrib import messages
from rest_framework.views import APIView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from rest_framework.renderers import TemplateHTMLRenderer
from django.db import connection, transaction
import uuid

# Create your views here.
#TO-DO : Sort by created at
class AllAuctionItems(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/all_items.html"

    def get(self,request):
        all_auctionable_items = []
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT i.name as name, i.description as description, i.static_id as itemid, images.image as image from item i INNER JOIN itemimages images ON images.item_id = i.static_id WHERE i.is_live = true AND i.is_sold = false AND i.end_time > '{timezone.now()}'")
            all_auctionable_items = dictfetchall(cursor)
        return render(request,self.template_name,context = {
            "items" : all_auctionable_items,
            "is_admin" : checkAdmin(request)
        })

#TO-DO : Change display layout : show last bid time, 
#Pass new context of bid_time and time.now() to the template.
class ItemDetailView(LoginRequiredMixin,APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/item_details.html"

    def get(self,request, pk):
        required_item =  None
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT i.static_id as itemid, i.name as name, i.end_time as end_time, i.is_sold as is_sold, i.is_live as is_live, i.current_bid as current_bid, images.image as image from item i INNER JOIN itemimages images ON i.static_id = images.item_id WHERE i.is_live = true AND i.is_sold = false AND i.static_id = '{pk}'")
            required_item = dictfetchall(cursor)
        if(required_item):
            return render(request,self.template_name,context = {
                "item" : required_item[0],
                "is_admin" : checkAdmin(request)
            })
        return render(request,self.template_name,context = {
        })


#Bids are placed through this view - Only users can place bids 
class BidOnItemView(RequestFromUserMixin,APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/bid_item.html"

    #Show a table of the previous bids on this page
    def get(self,request, pk):
        required_item = None
        all_item_bids = None
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT i.static_id as static_id, i.name as name, i.end_time as end_time, i.is_sold as is_sold, i.is_live as is_live, i.current_bid as current_bid from item i WHERE i.is_live = true AND i.is_sold = false AND i.static_id = '{pk}'")
            required_item = dictfetchall(cursor)
            cursor.execute(f"SELECT b.amount as amount, b.placed_at as placed_at, u.email as email from Bid b INNER JOIN UserProfile u ON b.placed_by_id = u.static_id AND b.item_id = '{pk}'")
            all_item_bids = dictfetchall(cursor)
        print(all_item_bids)
        return render(request,self.template_name,context = {
            "item" : required_item[0],
            "bids" : all_item_bids,
        })
    
    #Add messages section --> show bid success message and reload the bid page.
    def post(self, request, *args, **kwargs):
        item_static_id = kwargs["pk"]
        amount_bid = request.POST.get("bid")
        print(type(amount_bid))
        if not amount_bid:
            messages.error(request, "Bid amount not provided")
            return redirect('bid-on-item', pk = item_static_id)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM item where static_id = '{item_static_id}'")
            item = dictfetchall(cursor)
            if not item:
                messages.error(request, "Item Static ID invalid")
                return redirect('bid-on-item', pk = item_static_id)
            cursor.execute(f"SELECT * FROM userprofile where email = '{request.user.email}'")
            profile = dictfetchall(cursor)
            if not profile :
                messages.error(request, "Profile not found or invalid")
                return redirect('bid-on-item', pk = item_static_id)
            profile_static_id = profile[0]["static_id"]
            cursor.execute(f"SELECT * FROM bid where item_id = '{item_static_id}' AND amount = {amount_bid}")
            previous_bid_with_amount = dictfetchall(cursor)
        if previous_bid_with_amount:
            messages.error(request,"This amount has already been bid before")
            return redirect('bid-on-item', pk = item_static_id)
        if profile_static_id:
            messages.error(request,"This User does not exist")
            return redirect('bid-on-item', pk = item_static_id)
        new_bid = Bid.objects.create(item = Item.objects.filter(static_id = item_static_id).first(), amount = amount_bid, placed_by = UserProfile.objects.filter(static_id = profile_static_id))
        new_bid.save()
        # cursor.execute(f"INSERT into Bid(amount, item_id, placed_by_id) VALUES({int(amount_bid)}, '{item_static_id}', '{profile_static_id}')")
        return redirect('bid-on-item', pk = item_static_id)


#Show user details --> for admin just display that the person is an admin 
class UserProfileView(RequestFromUserMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/login.html"

    def get(self, request):
        pass


"""REGISTRATION VIEWS"""

class RegisterUser(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/register.html"

    def post(self,request):
        age = request.POST.get('age')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = User.objects.filter(email = email)
        if not user :
            # query = f"insert into UserProfile (age, email, password, registration_date) values ({age},'{email}','{password}','{timezone.now()}')"
            # with connection.cursor() as cursor:
            #     cursor.execute(query)
            #     connection.commit()
            profile = UserProfile.objects.create(age = age, email = email, password = password)
            user = User.objects.create_user(username=email.split("@")[0],password=password,email=email, first_name = first_name, last_name = last_name)
            return redirect('login')
        else:
            messages.error(request, "This user is already registered")
            return redirect("register")

    def get(self,request):
        context = {}
        context['is_admin'] = False
        return render(request,self.template_name,context=context)


class LoginView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/login.html"

    def post(self,request):
        email = request.POST.get("email")
        password = request.POST.get("password")
        user_profile_query = f"SELECT count(*) as count from UserProfile where email = '{email}' and password = '{password}'"
        admin_query = f"SELECT count(*) as count from Admin where email = '{email}' and password = '{password}'"
        with connection.cursor() as cursor:
            cursor.execute(user_profile_query)
            user_profile = dictfetchall(cursor)
            cursor.execute(admin_query)
            admin = dictfetchall(cursor)
        if not(user_profile[0]["count"] or admin[0]["count"]) :
            messages.error(request, "This user is not registered. Register below")
            return redirect('register')
        else:
            username = email.split("@")[0]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if admin[0]["count"]:
                    return redirect('create-item')
                return redirect('all-items')
            messages.error(request,"No such user! Register yourself")
            return redirect('register')

    def get(self,request):
        return render(request, self.template_name)

def logout_view(request):
    logout(request)
    return redirect('login')


#View from which an admin can edit an added item (any admin can change any item --> not limited to the one who created it)
class EditItem(RequestFromAdminMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/login.html"

    def get(self, request):
        pass

#TO-DO : Re-direct to error page or profile page with required error messages
#TO-DO : Add input validation for final date.
class CreateItemView(RequestFromAdminMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auction/create_item.html"

    def get(self, request):
        categories = []
        with connection.cursor() as cursor:
            cursor.execute("Select static_id, name from category")
            categories = dictfetchall(cursor)
        print(categories)
        return render(request,self.template_name, context = {
            "categories" :  categories,
            "is_admin" : True,
            "now" : timezone.now()
        })
    
    def post(self, request):
        item_name = request.POST.get("name")
        item_desc = request.POST.get("description")
        item_reserve_price = request.POST.get("reserve_price")
        item_minimum_bid = request.POST.get("minimum_bid")
        item_bid_increment = request.POST.get("bid_increment")
        item_end_time = request.POST.get("end_time")
        item_category_static_id = request.POST.get("category")
        admin_query = f"SELECT static_id from Admin where email = '{request.user.email}'"
        with connection.cursor() as cursor:
            cursor.execute(admin_query)
            admin = dictfetchall(cursor)
        if not admin:
            #Re-direct to error page with message
            messages.error(request,"You are not an Admin, you cannot add items to this auction")
            redirect('login')
        if not (item_name or item_reserve_price or item_minimum_bid or item_bid_increment or item_end_time or item_category_static_id) :
            messages.error(request, "Insufficient Fields")
            return redirect('create-item')
        admin_static_id = admin[0]["static_id"]
        #Add atomic transactions here
        with transaction.atomic():
            item = Item.objects.create(name = item_name, description = item_desc, reserve_price = item_reserve_price, minimum_bid = item_minimum_bid, bid_increment = item_bid_increment, end_time = item_end_time, current_bid = item_minimum_bid, category = Category.objects.filter(static_id = item_category_static_id).first(), added_by = Admin.objects.filter(static_id = admin_static_id).first())
            item.save()
            ItemImage.objects.create(image = request.FILES["upload"], item = item)
        messages.success(request,"Item Created Successfully")
        return redirect("all-items")
        # new_item_id = uuid.uuid4()
        # with connection.cursor() as cursor:
        #     cursor.execute(f"INSERT into item(static_id, name, description, reserve_price, minimum_bid, bid_increment, end_time, category_id, added_by_id, is_sold, is_live, start_time, current_bid) VALUES('{new_item_id}','{item_name}','{item_desc}',{item_reserve_price},{item_minimum_bid},{item_bid_increment},'{item_end_time}','{item_category_static_id}','{admin_static_id}', {False}, {True}, '{timezone.now()}',{item_minimum_bid})")
        #     transaction.commit()
        pass

def dictfetchall(cursor): 
    "Returns all rows from a cursor as a dict" 
    desc = cursor.description 
    return [
            dict(zip([col[0] for col in desc], row)) 
            for row in cursor.fetchall() 
    ]

def checkAdmin(request):
    admin = Admin.objects.filter(email = request.user.email)
    if admin:
        return True
    else :
        return False