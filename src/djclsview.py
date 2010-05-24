# -*- coding: utf-8 -*-

__version__ = '0.0.1'

from functools import partial, wraps

__all__ = ['View']


class View(object):
    
    """
    Abstract superclass for class-based views.
    
    Class-based views (CBVs) are classes which behave in a similar way to Django
    view functions. The underlying requirement for Django views is that they map
    requests to responses; by using classes, we get the benefits of inheritance
    to reduce boilerplate and increase reusability. There are many approaches to
    class-based views; this particular approach trades a slight performance and
    memory footprint for simplicity and thread-safety.
    
    You can point to a class-based view directly from the URLconf:
    
        urlpatterns = patterns('',
            ...
            url(r'^view/$', 'myapp.views.MyView', name='my-view'),
            ...
        )
    
    To replicate the behavior of a function, `__new__()` has been overridden;
    calling `ClassName(request, *args, **kwargs)` will instantiate the class and
    then call the object (i.e. `obj.__call__()`), returning whatever that method
    returns (which should be a `django.http.HttpResponse` instance). Thus, at
    the highest level, view classes may be used identically to view functions.
    
    Since usual instantiation has been modified, you can instantiate a view
    class with `ViewClass._new(request, *args, **kwargs)`. This might be useful
    if you need to access functionality defined on another view class (although
    a separate utility class or mixin is usually a better idea for shared
    functionality).
    
    Some points to note about this implementation:
    
    *   The `__new__()` method has been overridden to immediately call the
        instance after creation. You shouldn't need to touch this in a subclass.
    
    *   The request processing is carried out in two phases:
        
        *   **Initialization**: the `__init__()` method is called on an instance
            of the view class, with all the arguments passed in from the URLconf
            (i.e. `(self, request, *args, **kwargs)`). By default this stores
            the request, positional and keyword arguments on the instance as
            `self.request`, `self.args` and `self.kwargs` respectively.
        
        *   **Response**: the `__call__()` method is called without any
            arguments (except `self`). This should return an instance of
            `django.http.HttpResponse`.
    
    *   Decorators on instance methods need to be wrapped with
        `django.utils.decorators.method_decorator()`:
        
            from somemodule import some_decorator
            from django.utils.decorators import method_decorator
            
            class MyView(View):
                
                @method_decorator(some_decorator)
                def method(self):
                    return something()
    
    Examples
    ========
    
    Simple view definition and invocation:
    
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
        >>> view  # doctest: +ELLIPSIS
        <...MyView object at 0x...>
    
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
    
    """
    
    def __new__(cls, request, *args, **kwargs):
        instance = cls._new(request, *args, **kwargs)
        return instance()
    
    @classmethod
    def _new(cls, *args, **kwargs):
        
        """
        Create a normal instance of this class.
        
        This method does pretty much exactly what the usual instance creation
        mechanism does; it exists because `__new__()` has been overridden so
        that this class can be used as a view.
        """
        
        instance = object.__new__(cls)
        if isinstance(instance, cls):
            instance.__init__(*args, **kwargs)
        return instance
    
    @classmethod
    def _decorate(cls, *decorators):
        
        """
        Decorate this class-based view with one or more decorators.
        
        This method takes one or more decorators, and returns a new class, with
        those decorators safely applied in reverse order.
        
        This method exists to alleviate one of the main problems when mixing
        class-based views with decorators. Most decorators return some sort of
        wrapper function; if you call such a decorator on a class, you won't be
        able to inherit from it. This method fixes that problem by wrapping the
        `__new__()` static method with the decorator, and returning that as part
        of a new class.
        
        Example:
        
            >>> class X(View):
            ...     def __call__(self):
            ...         print 'invoking'
            ...         print 'request:', self.request
            
            >>> _ = X('Request')
            invoking
            request: Request
            
            >>> def decorator(func):
            ...     def wrapper(*args, **kwargs):
            ...         print 'wrapping'
            ...         return func(*args, **kwargs)
            ...     return wrapper
            
            >>> _ = X._decorate(decorator)('Request')
            wrapping
            invoking
            request: Request
        
        """
        
        for decorator in decorators[::-1]:
            cls = type(cls.__name__, (cls,), {
                '__new__': staticmethod(method_decorator(decorator)(cls.__new__)),
            })
        return cls
    
    # You might need to override this method.
    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
    
    # You definitely need to override this method.
    def __call__(self):
        raise NotImplementedError('Need to define __call__() on this view.')


def method_decorator(decorator):
    
    """
    Wrap a function decorator as a method decorator.
    
    A lot of decorators in Python are written to depend on a set order of
    positional arguments. In Django, for example, all of the built-in decorators
    expect the first argument to be a `request` object. If you're writing a
    typical class-based view, the first argument will be `self`, so you won't be
    able to use the standard decorators. Until now!
    
    `methodist()` wraps a function decorator to produce a new method decorator.
    Use it like this:
    
        class MyClassBasedView(object):
            
            @methodist(login_required)
            def __call__(self, request, *args, **kwargs):
                do_something()
    
    Full Example
    ============
    
        >>> class X(object):
        ...     def meth(self, a, b):
        ...         return a + b
        
        >>> X().meth(1, 2)
        3
    
    A standard decorator for a binary operator might look like this:
    
        >>> def mult_2(func):
        ...     def wrapper(a, b):
        ...         return func(a * 2, b * 2)
        ...     return wrapper
    
    It works fine for a standard function:
    
        >>> @mult_2
        ... def func(a, b):
        ...     return a + b
        >>> func(1, 2)
        6
    
    But we can't use that directly inside a class:
    
        >>> class Y(object):
        ...     @mult_2
        ...     def meth(self, a, b):
        ...         return a + b
        
        >>> Y().meth(1, 2)
        Traceback (most recent call last):
        ...
        TypeError: wrapper() takes exactly 2 arguments (3 given)
    
    But using `@method_decorator`, we can:
    
        >>> class Z(object):
        ...     @method_decorator(mult_2)
        ...     def meth(self, a, b):
        ...         return a + b
        
        >>> Z().meth(1, 2)
        6
    
    """
    
    @wraps(decorator)
    def decoratorwrapper(method):
        @wraps(method)
        def methodwrapper(self, *args, **kwargs):
            return decorator(partial(method, self))(*args, **kwargs)
        return methodwrapper
    return decoratorwrapper


if __name__ == '__main__':
    import doctest
    doctest.testmod()
