# Deployment Guide for PDF Toolkit

This guide will walk you through the process of adding your PDF Toolkit to GitHub and deploying it on Vercel.

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in to your account.
2. Click on the "+" icon in the top-right corner and select "New repository".
3. Name your repository (e.g., "pdf-toolkit").
4. Add a description (optional).
5. Choose whether to make the repository public or private.
6. Do NOT initialize the repository with a README, .gitignore, or license.
7. Click "Create repository".

## Step 2: Initialize Git and Push to GitHub

Open a command prompt or terminal in the PDF-Toolkit directory and run the following commands:

```bash
# Initialize Git repository
git init

# Add all files to the staging area
git add .

# Commit the changes
git commit -m "Initial commit"

# Add the remote repository URL (replace 'yourusername' with your GitHub username)
git remote add origin https://github.com/yourusername/pdf-toolkit.git

# Push to GitHub
git push -u origin master
```

## Step 3: Deploy on Vercel

1. Go to [Vercel](https://vercel.com) and sign in with your GitHub account.
2. Click on "New Project".
3. Select the "pdf-toolkit" repository from the list.
4. Configure the project:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: None
   - Output Directory: None
5. Add the following environment variables if needed:
   - EMAIL_HOST
   - EMAIL_PORT
   - EMAIL_USER
   - EMAIL_PASSWORD
   - EMAIL_FROM
6. Click "Deploy".

## Step 4: Verify Deployment

1. Once the deployment is complete, Vercel will provide you with a URL for your deployed application.
2. Click on the URL to verify that your PDF Toolkit is working correctly.

## Troubleshooting

If you encounter any issues during deployment, check the following:

1. Make sure all dependencies are listed in the `requirements.txt` file.
2. Check the Vercel deployment logs for any errors.
3. Ensure that the `vercel.json` file is correctly configured.
4. If you're using environment variables, make sure they're set correctly in the Vercel dashboard.

## Updating Your Deployment

To update your deployment after making changes to your code:

1. Make your changes locally.
2. Commit the changes:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```
3. Push to GitHub:
   ```bash
   git push origin master
   ```
4. Vercel will automatically redeploy your application.