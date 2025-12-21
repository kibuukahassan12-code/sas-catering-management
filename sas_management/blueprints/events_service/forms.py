from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, DateTimeField, SelectField
from wtforms.validators import DataRequired, Optional

class ServiceForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    price = DecimalField("Base Price", validators=[Optional()], places=2)

class ServiceItemForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    unit_price = DecimalField("Unit Price", validators=[Optional()], places=2)

class ServiceTaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    assigned_to = SelectField("Assign to", coerce=int, validators=[Optional()])
    status = SelectField("Status", choices=[("Pending","Pending"),("In Progress","In Progress"),("Completed","Completed")])
    due_date = DateTimeField("Due Date", format="%Y-%m-%d %H:%M", validators=[Optional()])

