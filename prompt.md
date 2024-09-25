I want to organize a trasure hunt in a city and I want to build a webapp to use it for this purpose. The trasure hunt will be attended by children and they will be split into groups.

Here are the requirements for the webapp:
1. I want it in python with django or flask.
2. When a group of children reaches a location, I want them to scan a QR code which is a link to the app. The link should lead to a question (as a form) and should have the group number as a GET parameter.
3. There should be 40 forms. Each form is a simple question with either a dropdown box with 3 options or a textbox. The logic behind the form should also evaluate the answer and calculate the points for the answer.
4. When they answer a form, the answer needs to be stored in a database (sqlite) with the following fields: group number, question number, answer, points earned, timestamp.
5. They should have the possibility to see the answer if they already answered a quesion and to be able to change the answer.
6. There should also be an admin page where I need to have the following feaures:
    - I want to be able to clear the whole database from a button
    - I want to see each group how many points it has, how many answers did they provided. They should also receive a number of points in the order of finishing the questions.
Can you please show me first your intended design for this webapp?

https://chatgpt.com/share/66f02539-3e60-8000-9c83-12249bc938db

