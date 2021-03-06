import webapp2
import json
import os
import jinja2
import datetime
import time
import math
from food_items import FoodItem
import logging
from food_items import User
from google.appengine.ext import ndb
from google.appengine.api import users


f = open('client_secret.json', 'r')
client_secrets =json.loads(f.read())
f.close()



current_jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

current_food_information = {}


class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        loggedin_user = users.get_current_user()
        if loggedin_user:
            time.sleep(.25)
            self.redirect('/homepage')
        else:
            welcome_template = current_jinja_environment.get_template('templates/welcome.html')
            self.response.write(welcome_template.render())



class LoginHandler(webapp2.RequestHandler):
    def get(self):
        loggedin_user = users.get_current_user()


        if loggedin_user:
            current_users = User.query().filter(User.id == loggedin_user.user_id()).fetch()
            x = []
            if current_users == x:
                template = current_jinja_environment.get_template('templates/signup.html')
                self.response.write(template.render())
            else:
                template = current_jinja_environment.get_template('templates/home.html')
                self.response.write(template.render({'logout_link': users.create_logout_url('/')}))
        else:
            login_prompt_template = current_jinja_environment.get_template('templates/login.html')
            self.response.write(login_prompt_template.render({'login_link': users.create_login_url('/login-page')}))


class MakeUserHandler(webapp2.RequestHandler):
    def post(self):
        user = User(first_name = self.request.get('name'), id = users.get_current_user().user_id())
        user.put()
        time.sleep(.25)
        self.redirect('/homepage')

class HomePageHandler(webapp2.RequestHandler):
    def get(self):
            home_template = current_jinja_environment.get_template('templates/home.html')
            self.response.write(home_template.render({'logout_link': users.create_logout_url('/')}))


class AddFoodHandler(webapp2.RequestHandler):
    def post(self):
        template_vars= {
        'client_id':client_secrets['web']['client_id'],
        'api_key':client_secrets['web']['api_key'],
        }
        food_template = current_jinja_environment.get_template('/templates/food.html')

        self.response.write(food_template.render(template_vars))



class FoodConfirmHandler(webapp2.RequestHandler):
    def post(self):
        exp_date_list = self.request.get('exp-date').split('/')
        temp1 = exp_date_list[2]+'-'+exp_date_list[0]+'-'+exp_date_list[1]+'T09:00:00-07:00'
        temp2 = exp_date_list[2]+'-'+exp_date_list[0]+'-'+exp_date_list[1]+'T17:00:00-07:00'

        template_vars = {
            'food_type': self.request.get('food-type'),
            'food_name': self.request.get('food-name'),
            'bought_date': self.request.get('bought-date'),
            'exp_date': self.request.get('exp-date'),
            'format1': temp1,
            'format2': temp2,
            'client_id':client_secrets['web']['client_id'],
            'api_key':client_secrets['web']['api_key'],
        }

        current_food_information['food_type'] = self.request.get('food-type')
        current_food_information['food_name'] = self.request.get('food-name')
        current_food_information['bought_date'] = self.request.get('bought-date')
        current_food_information['exp_date'] = self.request.get('exp-date')
        confirm_template = current_jinja_environment.get_template('/templates/confirm.html')

        self.response.write(confirm_template.render(template_vars))


#class ConfirmedHandler(webapp2.RequestHandler):
class ConfirmedHandler(webapp2.RequestHandler):
    def post(self):
        bought_date_list = current_food_information['bought_date'].split('/')
        exp_date_list = current_food_information['exp_date'].split('/')

        FoodItem(user_id=str(users.get_current_user().user_id()), food_type=current_food_information['food_type'], food_name=current_food_information['food_name'],\
            buy_month=int(bought_date_list[0]), buy_date=int(bought_date_list[1]), buy_year=int(bought_date_list[2]),\
            exp_month=int(exp_date_list[0]), exp_date=int(exp_date_list[1]), exp_year=int(exp_date_list[2])).put()
        confirmed_template = current_jinja_environment.get_template('/templates/confirmed.html')
        self.response.write(confirmed_template.render())

class ListFoodHandler(webapp2.RequestHandler):
    def get(self):
        food_item_query = FoodItem.query().filter(FoodItem.user_id==str(users.get_current_user().user_id()))
        food_exp_calc = {'exp':[], 'month':[], 'week':[], 'day':[]}
        food_list_dict = {'get_list': '', 'get_day': '', 'get_week': '', 'get_month': '', 'get_exp': ''}

        for food_item in food_item_query:
            str_temp = "<tr>"
            str_temp+=('<td>'+food_item.food_type+'</td>')
            str_temp+=('<td>'+food_item.food_name+'</td>')
            now_time = datetime.datetime.now()
            bought_time = datetime.datetime(food_item.buy_year, food_item.buy_month, food_item.buy_date)
            exp_time = datetime.datetime(food_item.exp_year, food_item.exp_month, food_item.exp_date)

            if now_time>=exp_time:
               if food_item not in food_exp_calc['exp']:
                    food_exp_calc['exp'].append(food_item)
            elif (exp_time - now_time).days == 1:
                if food_item not in food_exp_calc['day']:
                   food_exp_calc['day'].append(food_item)

            elif (exp_time - now_time).days <= 7:
                if food_item not in food_exp_calc['week']:
                    food_exp_calc['week'].append(food_item)
            elif (exp_time - now_time).days <= 30:
                if food_item not in food_exp_calc['month']:
                    food_exp_calc['month'].append(food_item)

            str_temp+=('<td>'+str(food_item.buy_month)+'/'+str(food_item.buy_date)+'/'+str(food_item.buy_year)+'</td>')
            str_temp+=('<td>'+str(food_item.exp_month)+'/'+str(food_item.exp_date)+'/'+str(food_item.exp_year)+'</td>')

            if now_time>=exp_time or bought_time>=exp_time:
                str_temp+=("<td><p class='red'>"+str(True)+"</p></td>")
            else:
                str_temp+=("<td><p  class='green'>"+str(False)+"</p></td>")
            str_temp+=("<td><form method='post' action='/remove'> <input type='hidden' name='food_item_key' value=" + str(food_item.key.id()) + "><input type='submit' value='Remove' ></form></td>")
            str_temp+='</tr>'
            food_list_dict['get_list']+=str_temp

        for food_item in food_exp_calc['exp']:
            str_temp = '<tr>'
            str_temp+=('<td>'+food_item.food_type+'</td>')
            str_temp+=('<td>'+food_item.food_name+'</td>')
            str_temp+=('<td>0</td>')
            food_list_dict['get_exp']+=str_temp

        for food_item in food_exp_calc['day']:
            str_temp = '<tr>'
            str_temp+=('<td>'+food_item.food_type+'</td>')
            str_temp+=('<td>'+food_item.food_name+'</td>')
            str_temp+=('<td>1</td>')
            food_list_dict['get_day']+=str_temp

        for food_item in food_exp_calc['week']:
            now_time = datetime.datetime.now()
            exp_time = datetime.datetime(food_item.exp_year, food_item.exp_month, food_item.exp_date)
            str_temp = '<tr>'
            str_temp+=('<td>'+food_item.food_type+'</td>')
            str_temp+=('<td>'+food_item.food_name+'</td>')
            str_temp+=('<td>'+ str(math.fabs((now_time - exp_time).days)) + '</td>')
            food_list_dict['get_week']+=str_temp

        for food_item in food_exp_calc['month']:
            now_time = datetime.datetime.now()
            exp_time = datetime.datetime(food_item.exp_year, food_item.exp_month, food_item.exp_date)
            str_temp = '<tr>'
            str_temp+=('<td>'+food_item.food_type+'</td>')
            str_temp+=('<td>'+food_item.food_name+'</td>')
            str_temp+=('<td>'+ str(math.fabs((now_time - exp_time).days)) + '</td>')
            food_list_dict['get_month']+=str_temp



        list_template = current_jinja_environment.get_template('/templates/listFood.html')
        self.response.write(list_template.render(food_list_dict))





class RemoveHandler(webapp2.RequestHandler):
    def post(self):
        food_item_key = self.request.get('food_item_key')
        for item in FoodItem.query():
            if str(item.key.id())==food_item_key:
                item.key.delete()
        delete_template = current_jinja_environment.get_template('/templates/delete.html')
        self.response.write(delete_template.render())













app = webapp2.WSGIApplication([
    #('/', MainHandler),
    ('/', WelcomeHandler),
    ('/login-page', LoginHandler),
    ('/homepage', HomePageHandler),
    ('/make-user', MakeUserHandler),
    ('/add-food', AddFoodHandler),
    ('/list-food', ListFoodHandler),
    ('/confirm', FoodConfirmHandler),
    ('/confirmed', ConfirmedHandler),
    ('/remove', RemoveHandler),
])
