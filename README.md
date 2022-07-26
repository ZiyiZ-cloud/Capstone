# YourPet

### A Web application that allows users to easily check local pets that are available for adoption within the US. The website is deployed in the following link: https://your-pet.herokuapp.com/ 

## App Features Include:

User can select either to check available dogs or cats and then narrow down the result by entering the zipcode and radius. This will provide a list of results back to user with basic information for the pets. User can also click into each pet and view more information about the pet.

For each pet, users can view all available photos, basic info, attributes, and contact information. The web allow user to access the pets information as guest or logged in user. The guest can access most of the pets' information except the contact information to reach out to the adoption center. 

Once logged in, user would be able to see the contact information and also add their favorite ones into the personal list that is available to broswer in the userprofile page.

<img width="1440" alt="Screen Shot 2022-07-26 at 4 27 24 PM" src="https://user-images.githubusercontent.com/82247271/181105739-05b86936-6fb5-4961-95d6-761967ec64d0.png">

## Resources Used:
Petfinder data: https://www.petfinder.com/developers/v2/docs/

This API provide essential data support this application. The app will make API call to get data for pets based on zipcode and range and return all the pets information regarding their photos, basic conditions, and location to adopt them.

## Technology Used:
* Python/Flask,
* PostgreSQL
* SQLAlchemy
* Heroku
* RESTful APIs
* HTML
* CSS
* WTForms

