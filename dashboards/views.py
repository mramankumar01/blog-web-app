from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import auth, messages  # Import messages framework
from django.db import IntegrityError  # Import to catch database constraint violations
from blogs.models import Blog, Category
from django.contrib.auth.decorators import login_required
from .forms import AddUserForm, BlogPostForm, CategoryForm, EditUserForm
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User

# Create your views here.
@login_required(login_url='login')
def dashboard(request):
    category_count = Category.objects.all().count()
    blogs_count = Blog.objects.all().count()
    context = {
        'category_count': category_count,
        'blogs_count': blogs_count,
    }
    return render(request, 'dashboard/dashboard.html', context)

def categories(request):
    return render(request, 'dashboard/categories.html')


# def add_category(request):
#     if request.method == 'POST':
#         form = CategoryForm(request.POST)
#         if form.is_valid:
#             form.save()
#             return redirect('categories')
#     form = CategoryForm()
#     context = {
#         'form': form,
#     }
#     return render(request, 'dashboard/add_category.html', context)


def add_category(request):
    """
    View to add a new category with proper validation and error handling.
    
    Handles:
    - Form validation
    - Database constraint violations (duplicate categories)
    - Success/error messages
    - Proper redirect after successful save
    """
    
    if request.method == 'POST':
        # User submitted the form
        form = CategoryForm(request.POST)
        
        # ====================================================================
        # BUG FIX: You wrote "form.is_valid" (missing parentheses!)
        # ====================================================================
        # WRONG: if form.is_valid:      ← This is a method reference, not a call
        # RIGHT: if form.is_valid():    ← This actually calls the method
        #
        # Without (), Python just checks if the method exists (always True!)
        # So invalid forms were being saved, causing errors
        if form.is_valid():  # ← Notice the parentheses ()
            
            # ================================================================
            # TRY-EXCEPT BLOCK: Catch database constraint violations
            # ================================================================
            try:
                # Attempt to save the category to the database
                # This is where the constraint violation will occur if duplicate exists
                category = form.save()  # Save and capture the created object
                
                # ------------------------------------------------------------
                # SUCCESS: Category saved successfully
                # ------------------------------------------------------------
                # Add a success message to display on the next page
                # messages.success() creates a one-time message
                # It will be displayed in the template using {% if messages %}
                messages.success(
                    request, 
                    f'Category "{category.category_name}" added successfully!'
                )
                
                # Redirect to the categories list page
                # PRG Pattern: Post-Redirect-Get prevents form resubmission
                # If user refreshes the page, they won't accidentally create duplicates
                return redirect('categories')
                
            except IntegrityError as e:
                # ------------------------------------------------------------
                # ERROR: Database constraint violation caught
                # ------------------------------------------------------------
                # This exception is raised when:
                # - Duplicate category name (case-insensitive)
                # - Any other database constraint violation
                
                # Convert exception to string to check error details
                error_str = str(e)
                
                # Check if it's our specific unique constraint
                if 'unique_category_name_ci' in error_str:
                    # This is the duplicate category error
                    
                    # OPTION 1: Add error directly to the form field
                    # This makes the error appear next to the category_name input
                    form.add_error(
                        'category_name',  # Field name to attach error to
                        'This category already exists (case-insensitive match).'
                    )
                    
                    # OPTION 2: Also add as a Django message (optional, choose one or both)
                    # This appears in the messages block at the top of the page
                    messages.error(
                        request, 
                        'A category with this name already exists!'
                    )
                
                else:
                    # Some other database constraint error
                    # Add as a general form error (not tied to specific field)
                    form.add_error(
                        None,  # None means it's a general form error
                        'Unable to save category. Please try again.'
                    )
                    messages.error(
                        request, 
                        'An unexpected database error occurred.'
                    )
                
                # Don't return here - let the code fall through to render the form
                # with the errors displayed
            
            except Exception as e:
                # ------------------------------------------------------------
                # CATCH-ALL: Any other unexpected errors
                # ------------------------------------------------------------
                form.add_error(
                    None, 
                    f'An unexpected error occurred: {str(e)}'
                )
                messages.error(request, 'Something went wrong. Please try again.')
        
        else:
            # ================================================================
            # FORM VALIDATION FAILED
            # ================================================================
            # form.is_valid() returned False
            # This means the form has validation errors (empty field, etc.)
            # The errors are already in form.errors, crispy will display them
            
            # Add a general message to alert the user
            messages.error(request, 'Please correct the errors below.')
    
    else:
        # ====================================================================
        # GET REQUEST: Display empty form
        # ====================================================================
        # User is visiting the page for the first time
        # Create a blank form for them to fill out
        form = CategoryForm()
    
    # ========================================================================
    # RENDER THE TEMPLATE
    # ========================================================================
    # This happens in three scenarios:
    # 1. GET request: Show empty form
    # 2. POST with validation errors: Show form with errors
    # 3. POST with database error: Show form with error messages
    #
    # Only successful saves redirect away (don't reach this line)
    context = {
        'form': form,  # Form object (may contain errors)
    }
    return render(request, 'dashboard/add_category.html', context)


def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('categories')
    form = CategoryForm(instance=category)
    context = {
        'form': form,
        'category': category,
    }
    return render(request, 'dashboard/edit_category.html', context)


def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('categories')


def posts(request):
    posts = Blog.objects.all()
    context = {
        'posts': posts,
    }
    return render(request, 'dashboard/posts.html', context)


def add_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False) # temporarily saving the form
            post.author = request.user
            post.save()
            title = form.cleaned_data['title']
            post.slug = slugify(title) + '-'+str(post.id)
            post.save()
            return redirect('posts')
        else:
            print('form is invalid')
            print(form.errors)
    form = BlogPostForm()
    context = {
        'form': form,
    }
    return render(request, 'dashboard/add_post.html', context)


def edit_post(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            title = form.cleaned_data['title']
            post.slug = slugify(title) + '-'+str(post.id)
            post.save()
            return redirect('posts')
    form = BlogPostForm(instance=post)
    context = {
        'form': form,
        'post': post
    }
    return render(request, 'dashboard/edit_post.html', context)


def delete_post(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    post.delete()
    return redirect('posts')


def users(request):
    users = User.objects.all()
    context = {
        'users': users,
    }
    return render(request, 'dashboard/users.html', context)


def add_user(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users')
        else:
            print(form.errors)
    form = AddUserForm()
    context = {
        'form': form,
    }
    return render(request, 'dashboard/add_user.html', context)


def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users')
    form = EditUserForm(instance=user)
    context = {
        'form': form,
    }
    return render(request, 'dashboard/edit_user.html', context)


def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    return redirect('users')