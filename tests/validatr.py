import string

def pathjoin(path1, path2):
    arr = []
    if path1: arr.append(path1)
    if path2: arr.append(path2)
    return string.join(arr, '.')

class Undefined:
    pass

class Context(dict):
    def __init__(self, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        self.errors = []
        self.displayErrors = True

    def appendError(self, path, msg):
        if self.displayErrors:
            self.errors.append( (path, msg) )

class Validator(object):
    """
    """

    def __init__(self, *args):
        self.parseArgs(args)

    def validate(self, node, ctx=Context(), path=''):
        """ Perform standard validation.
        """

        if self.assign:
            ctx[self.assign] = node

        if self.validation:
            res = self.validation(node, ctx)
            if not res:
                ctx.appendError(path, "validation not passed")
            return res

        return True

    def parseArgs(self, args):
        """ Extract the validation and assignment from the arguments
            and pop the corresponding items from the arguments array.

            Return the array cleaned from those values
        """
        self.validation = None
        self.assign = None

        ar = []
        for a in args:
            if callable(a):
                self.validation = a
                continue

            if isinstance(a, unicode) or isinstance(a, str):
                self.assign = a
                continue
            
            ar.append(a)
        return ar

    def assign(self, node, ctx):
        """ Assign a variable in the context.
        """
        ctx[self.assign] = node

################ Types #####################

class SimpleValidator(Validator):

    def __init__(self, *args):
        if len(self.parseArgs(args)) is not 0:
            raise Exception("Useless parameters")

    def validate(self, node, ctx=Context(), path=''):
        res = self._validate(node)
        if not res:
            ctx.appendError(path, "not the correct type")

        return res and super(SimpleValidator, self).validate(node, ctx, path)

    def _validate(self, node):
        raise NotImplemented("Not implemented")

class TDate(SimpleValidator):
    """ A Date.
    """
    pass

class TBoolean(SimpleValidator):
    def _validate(self, node):
        return node is True or node is False

class TNumber(SimpleValidator):
    """ A Number
    """
    def _validate(self, node):
        return (isinstance(node, int) or isinstance(node, float)) and not isinstance(node, bool)

class TString(SimpleValidator):
    """ A String
    """
    def _validate(self, node):
        return isinstance(node, unicode) or isinstance(node, str)

class TUndefined(SimpleValidator):
    def _validate(self, node):
        return node is Undefined

class TNull(SimpleValidator):
    def _validate(self, node):
        return node is None
        
#########################################################

class TProperties(Validator):
    def __init__(self, *args):
        self.properties = args

    def validate(self, node, ctx=Context(), path=''):
        res = True
        for p in self.properties:
            res = p.validate(node, ctx, path) and res
        return res

class TProperty(Validator):
    def __init__(self, name, typ, *args):
        self.typ = typ
        self.name = name
        self.parseArgs(args)

    def validate(self, node, ctx=Context(), path=''):
        path = pathjoin(path, self.name)
        prop = node.get(self.name, Undefined)
        return self.typ.validate(prop, ctx, path) and \
            super(TProperty, self).validate(prop, ctx, path)

class TObject(Validator):
    """ An Object, that can contain properties.
    """

    def __init__(self, *args):
        args = self.parseArgs(args)

        self.properties = args

    def validate(self, node, ctx=Context(), path=''):
        if not hasattr(node, "iteritems"):
            ctx.appendError(path, "not an object")
            return False

        res = True
        for o in self.properties:
            res = o.validate(node, ctx, path) and res

        return super(TObject, self).validate(node, ctx, path) and res

class TArray(Validator):
    def __init__(self, typ=None, *args):
        args = self.parseArgs(args)
        if len(args) > 0:
            raise Exception("Left overs...")
        self.typ = typ

    def validate(self, node, ctx=Context(), path=''):
        if not hasattr(node, "__iter__") or hasattr(node, "iteritems"):
            ctx.appendError(path, "not an array")
            return False

        res = True
        if self.typ:
            for idx, o in enumerate(node):
                res = self.typ.validate(o, ctx, pathjoin(path, unicode(idx))) and res

        return super(TArray, self).validate(node, ctx, path) and res
        

class TChoice(Validator):
    def __init__(self, *choices):
        self.choices = self.parseArgs(choices)

    def validate(self, node, ctx=Context(), path=''):
        # Inhibit the error reporting, since some
        # of the choices WILL fail.
        ctx.displayErrors = False

        found_one = False
        for c in self.choices:
            if found_one:
                break
            found_one = c.validate(node, ctx, path)

        ctx.displayErrors = True

        return super(TChoice, self).validate(node, ctx, path) and found_one


class TIf(Validator):
    def __init__(self, cond, then, otherwise=None):
        self.cond = cond
        self.then = then
        self.otherwise = otherwise

    def validate(self, node, ctx=Context(), path=''):
        if self.cond(node, ctx):
            return self.then.validate(node, ctx, path)
        else:
            if self.otherwise:
                return self.otherwise.validate(node, ctx, path)
        return True

