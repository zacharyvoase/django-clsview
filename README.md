# `django-clsview`

`django-clsview` is a library with yet another solution to the problem of
class-based views in Django.


## Installation

The usual:

    pip install django-clsview  # OR
    easy_install django-clsview

There’s no need to add `djclsview` to your `INSTALLED_APPS` setting.


## Usage

Class-based views (CBVs) are classes which behave in a similar way to Django
view functions. The underlying requirement for Django views is that they map
requests to responses; by using classes, we get the benefits of inheritance to
reduce boilerplate and increase reusability. There are many approaches to
class-based views; this particular approach trades a *very* slight performance
and memory footprint for simplicity and thread-safety.

You can point to a class-based view directly from the URLconf:

    urlpatterns = patterns('',
        ...
        url(r'^view/$', 'myapp.views.MyView', name='my-view'),
        ...
    )

To replicate the behavior of a function, `__new__()` has been overridden;
calling `ClassName(request, *args, **kwargs)` will instantiate the class and
then call the object (i.e. `obj.__call__()`), returning whatever that method
returns (which should be a `django.http.HttpResponse` instance). Thus, at the
highest level, view classes may be used identically to view functions.

Since usual instantiation has been modified, you can instantiate a view class
with `ViewClass._new(request, *args, **kwargs)`. This might be useful if you
need to access functionality defined on another view class (although a separate
utility class or mixin is usually a better idea for shared functionality).

Some points to note about this implementation:

*   The `__new__()` method has been overridden to immediately call the instance
    after creation. You shouldn't need to touch this in a subclass.

*   The request processing is carried out in two phases:
    
    *   **Initialization**: the `__init__()` method is called on an instance of
        the view class, with all the arguments passed in from the URLconf (i.e.
        `(self, request, *args, **kwargs)`). By default this stores the request,
        positional and keyword arguments on the instance as `self.request`,
        `self.args` and `self.kwargs` respectively.
    
    *   **Response**: the `__call__()` method is called without any arguments
        (except `self`). This should return an instance of
        `django.http.HttpResponse`.

*   Decorators on instance methods need to be wrapped with
    `django.utils.decorators.method_decorator()`:
    
        from somemodule import some_decorator
        from django.utils.decorators import method_decorator
        
        class MyView(View):
            
            @method_decorator(some_decorator)
            def method(self):
                return something()


## Examples

Simple view definition and invocation:

    >>> from djclsview import View
    >>> class MyView(View):
    ...     def __call__(self):
    ...         print self.request
    ...         print self.args
    ...         print self.kwargs
    
    >>> MyView('request', 'arg1', 'arg2', kwarg1='value', kwarg2='value')
    request
    ('arg1', 'arg2')
    {'kwarg1': 'value', 'kwarg2': 'value'}

Instantiating a view, sidestepping invocation:

    >>> view = MyView._new('request', 'argument', kwarg='value')
    >>> view
    <__main__.MyView object at 0x...>

Decorating a view with a view decorator:

    >>> def auth_required(func):
    ...     def wrapper(request, *args, **kwargs):
    ...         assert request['authenticated'], "Unauthenticated!"
    ...         return func(request, *args, **kwargs)
    ...     return wrapper
    
    >>> class MyProtectedView(View):
    ...     def __call__(self):
    ...         print 'invoking'
    
    >>> MyProtectedView = MyProtectedView._decorate(auth_required)
    
    >>> MyProtectedView({'authenticated': True})
    invoking
            
    >>> MyProtectedView({'authenticated': False})
    Traceback (most recent call last):
    ...
    AssertionError: Unauthenticated!


## (Un)license

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
