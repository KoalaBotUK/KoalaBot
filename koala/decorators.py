

def make_registering_decorator(foreign_decorator):
    """
        Returns a copy of foreignDecorator, which is identical in every
        way(*), except also appends a .decorator property to the callable it
        spits out.
    """
    def new_decorator(func):
        # Call to newDecorator(method)
        # Exactly like old decorator, but output keeps track of what decorated it
        R = foreign_decorator(func)  # apply foreignDecorator, like call to foreignDecorator(method) would have done
        R.decorator = new_decorator  # keep track of decorator
        #R.original = func         # might as well keep track of everything!
        return R

    new_decorator.__name__ = foreign_decorator.__name__
    new_decorator.__doc__ = foreign_decorator.__doc__
    # (*)We can be somewhat "hygienic", but newDecorator still isn't signature-preserving, i.e. you will not be able to get a runtime list of parameters. For that, you need hackish libraries...but in this case, the only argument is func, so it's not a big issue

    return new_decorator


def methods_with_decorator(cls, decorator):
    """
        Returns all methods in CLS with DECORATOR as the
        outermost decorator.

        DECORATOR must be a "registering decorator"; one
        can make any decorator "registering" via the
        makeRegisteringDecorator function.
    """
    for maybe_decorated in cls.__dict__.values():
        if hasattr(maybe_decorated, 'decorator') and maybe_decorated.decorator == decorator:
            print(maybe_decorated)
            yield maybe_decorated
