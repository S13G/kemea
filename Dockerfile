FROM python:3.9-alpine

# Create a folder for the app
WORKDIR /kemea

# Install PostgreSQL dependencies
RUN apk add --no-cache postgresql-dev gcc musl-dev

# Create a group and add a user to the group
RUN addgroup systemUserGroup && adduser -D -G systemUserGroup developer

# Grant executable permission to the group for the workdir
RUN chmod g+s /wejpal

# Switch to the user
USER developer

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=${SECRET_KEY}
ENV DATABASE_URL=${DATABASE_URL}
ENV CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME}
ENV CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY}
ENV CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET}
ENV EMAIL_HOST_USER=${EMAIL_HOST_USER}
ENV EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
ENV ADMIN_EMAIL=${ADMIN_EMAIL}
ENV ADMIN_PASSWORD=${ADMIN_PASSWORD}
ENV PORT=${PORT}

# Copy the requirements.txt file into the workdir
COPY ./requirements.txt requirements.txt

# Install the dependencies
RUN pip3 install -r requirements.txt

# Copy the Django project into the image
COPY . .

# Switch to the root user temporarily to set permissions
USER root

# Create the staticfiles directory and set permissions
RUN mkdir -p /kemea/staticfiles \
    && chown -R developer:systemUserGroup /wejpal/staticfiles \
    && chmod -R 775 /wejpal/staticfiles

# Switch back to the developer user
USER developer

# collectstatic without interactive input, perform migrations and create a superuser automatically
CMD python3 manage.py migrate --settings=$DJANGO_SETTINGS_MODULE && \
    python3 manage.py collectstatic --no-input --settings=$DJANGO_SETTINGS_MODULE && \
    python3 manage.py runserver 0.0.0.0:$PORT

