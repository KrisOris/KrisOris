from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, TextAreaField, IntegerField
from wtforms.validators import InputRequired, EqualTo, Optional, NumberRange


class RegistrationForm(FlaskForm):
    user_id= StringField("Username:", 
                         validators=[InputRequired()])
    password = PasswordField("Password:", 
                             validators=[InputRequired()])
    password2 = PasswordField("Confirm password:", 
                              validators=[InputRequired(), EqualTo("password") ])
    submit= SubmitField("Submit")

class LoginForm (FlaskForm):
    user_id = StringField("Username:",
                          validators=[InputRequired()])
    password = PasswordField("Password:",
                             validators=[InputRequired()])
    submit = SubmitField("Submit")


class CheckoutForm(FlaskForm):
    address = StringField("Address:", validators=[InputRequired()])
    city = StringField("City:", validators=[InputRequired()])
    postal_code = StringField("Postal Code:", validators=[InputRequired()])
    country = StringField("Country:", validators=[InputRequired()])
    redeem_points = IntegerField("Points to redeem:", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Place Order")


class AccountForm(FlaskForm):
    current_password = PasswordField("Current password:", validators=[InputRequired()])
    new_username = StringField("New username:", validators=[Optional()])
    new_password = PasswordField("New password:", validators=[Optional()])
    confirm_password = PasswordField("Confirm new password:", validators=[Optional(), EqualTo("new_password")])
    submit = SubmitField("Update Account")


class AddProductForm(FlaskForm):
    name = StringField("Name:", validators=[InputRequired()])
    price = FloatField("Price:", validators=[InputRequired(), NumberRange(min=0)])
    image_filename = StringField("Image filename:", validators=[InputRequired()])
    quantity = IntegerField("Quantity:", validators=[InputRequired(), NumberRange(min=0)])
    description = TextAreaField("Description:", validators=[Optional()])
    submit = SubmitField("Add Product")