from flask_bcrypt import Bcrypt

# this Bcrypt extension is used for encryption and decryption or hashing the password of user
# this needs to be shared across other scripts which are responsible for the registration, login, user credentials and
# not supposed to be initiated once and not multiple times in each script since the individual bcrypt will not gonna understand the context
bcrypt = Bcrypt()
