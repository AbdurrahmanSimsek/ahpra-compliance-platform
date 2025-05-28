from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL, Length, Optional
from urllib.parse import urlparse

class WebsiteForm(FlaskForm):
    name = StringField('Website Name', validators=[DataRequired(), Length(max=120)])
    url = StringField('Website URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Add Website')
    
    def validate_url(self, url):
        # Make sure URL has http:// or https:// prefix
        parsed_url = urlparse(url.data)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError('Please enter a valid URL including http:// or https://')

class ScheduleCheckForm(FlaskForm):
    frequency = SelectField('Check Frequency', 
                          choices=[('daily', 'Daily'), 
                                   ('weekly', 'Weekly'), 
                                   ('monthly', 'Monthly')])
    submit = SubmitField('Schedule Recurring Checks')
