# UCA App Deployment Guide

## Pre-Deployment Checklist ✅

Your application has been prepared for deployment with the following fixes:
- ✅ Security vulnerabilities resolved
- ✅ Production settings created
- ✅ Static files configured
- ✅ Deployment files created

## Easiest Deployment Options

### 1. Railway (Recommended - Easiest)

**Steps:**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect Django and deploy
6. Add environment variables in Railway dashboard:
   - `SECRET_KEY`: Generate a secure key
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `your-app-name.railway.app`

**Pros:**
- Zero configuration needed
- Automatic HTTPS
- Built-in database options
- Free tier available

### 2. Render

**Steps:**
1. Go to [render.com](https://render.com)
2. Sign up and connect GitHub
3. Click "New" → "Web Service"
4. Connect your repository
5. Use these settings:
   - **Build Command**: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn uca_project.wsgi:application`
   - **Environment**: Python 3
6. Add environment variables:
   - `SECRET_KEY`: Generate a secure key
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `your-app-name.onrender.com`

**Pros:**
- Simple setup
- Good free tier
- Automatic deployments

### 3. Heroku

**Steps:**
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   ```
5. Deploy: `git push heroku main`
6. Run migrations: `heroku run python manage.py migrate`

**Pros:**
- Well-documented
- Reliable platform

## Environment Variables Required

Create these environment variables in your deployment platform:

```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com
```

## Post-Deployment Steps

1. **Run migrations**: Most platforms handle this automatically
2. **Create superuser**: Access your deployed app and create an admin user
3. **Test functionality**: Verify all features work correctly
4. **Set up custom domain** (optional): Configure your own domain

## Troubleshooting

### Common Issues:
1. **Static files not loading**: Ensure `collectstatic` runs during build
2. **Database errors**: Check if migrations ran successfully
3. **Permission errors**: Verify file permissions in deployment platform

### Debug Mode:
If you need to debug, temporarily set `DEBUG=True` in environment variables, but remember to set it back to `False` for security.

## Security Notes

Your application now includes:
- ✅ Secure session cookies
- ✅ CSRF protection
- ✅ HTTPS redirect
- ✅ Security headers
- ✅ Proper secret key handling

## Support

If you encounter issues:
1. Check the deployment platform logs
2. Verify environment variables are set correctly
3. Ensure all dependencies are in requirements.txt
4. Test locally with production settings first
