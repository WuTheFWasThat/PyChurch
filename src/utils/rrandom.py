# RPython-friendly version of random

# modified from:
# https://bitbucket.org/pypy/pypy/src/default/pypy/rlib/rrandom.py

try:
    from pypy.rlib.rarithmetic import r_uint, intmask
except:
    def r_uint(x):
      return x
    def intmask(x):
      return x

N = 624
M = 397
MATRIX_A = r_uint(0x9908b0df) # constant vector a
UPPER_MASK  = r_uint(0x80000000) # most significant w-r bits
LOWER_MASK = r_uint(0x7fffffff) # least significant r bits
MASK_32 = r_uint(0xffffffff)
TEMPERING_MASK_A = r_uint(0x9d2c5680)
TEMPERING_MASK_B = r_uint(0xefc60000)
MAGIC_CONSTANT_A = r_uint(1812433253)
MAGIC_CONSTANT_B = r_uint(19650218)
MAGIC_CONSTANT_C = r_uint(1664525)
MAGIC_CONSTANT_D = r_uint(1566083941)

import math

NV_MAGICCONST = 4 * math.exp(-0.5)/math.sqrt(2.0)
TWOPI = 2.0*math.pi
LOG4 = math.log(4.0)
SG_MAGICCONST = 1.0 + math.log(4.5)
BPF = 53        # Number of bits in a float
RECIP_BPF = 2**-BPF


class Random(object):
    def __init__(self, seed=r_uint(0)):
        self.state = [r_uint(0)] * N
        self.index = 0
        self.init_genrand(seed)

    def seed(self, seed=0):
        self.__init__(r_uint(seed))
        
    def init_genrand(self, s):
        mt = self.state
        mt[0]= s & MASK_32
        for mti in range(1, N):
            mt[mti] = (MAGIC_CONSTANT_A *
                           (mt[mti - 1] ^ (mt[mti - 1] >> 30)) + r_uint(mti))
            # See Knuth TAOCP Vol2. 3rd Ed. P.106 for multiplier.
            # In the previous versions, MSBs of the seed affect
            # only MSBs of the array mt[].
            # for >32 bit machines 
            mt[mti] &= MASK_32
        self.index = N

    def init_by_array(self, init_key):
        key_length = len(init_key)
        mt = self.state
        self.init_genrand(MAGIC_CONSTANT_B)
        i = 1
        j = 0
        if N > key_length:
            max_k = N
        else:
            max_k = key_length
        for k in range(max_k, 0, -1):
            mt[i] = ((mt[i] ^
                         ((mt[i - 1] ^ (mt[i - 1] >> 30)) * MAGIC_CONSTANT_C))
                     + init_key[j] + r_uint(j)) # non linear
            mt[i] &= MASK_32 # for WORDSIZE > 32 machines
            i += 1
            j += 1
            if i >= N:
                mt[0] = mt[N - 1]
                i = 1
            if j >= key_length:
                j = 0
        for k in range(N - 1, 0, -1):
            mt[i] = ((mt[i] ^
                        ((mt[i - 1] ^ (mt[i - 1] >> 30)) * MAGIC_CONSTANT_D))
                     - i) # non linear
            mt[i] &= MASK_32 # for WORDSIZE > 32 machines
            i += 1
            if (i>=N):
                mt[0] = mt[N - 1]
                i = 1
        mt[0] = UPPER_MASK

    def genrand32(self):
        mag01 = [0, MATRIX_A]
        mt = self.state
        if self.index >= N:
            for kk in range(N - M):
                y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK)
                mt[kk] = mt[kk+M] ^ (y >> 1) ^ mag01[y & r_uint(1)]
            for kk in range(N - M, N - 1):
                y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK)
                mt[kk] = mt[kk + (M - N)] ^ (y >> 1) ^ mag01[y & r_uint(1)]
            y = (mt[N - 1] & UPPER_MASK) | (mt[0] & LOWER_MASK)
            mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ mag01[y & r_uint(1)]
            self.index = 0
        y = mt[self.index]
        self.index += 1
        y ^= y >> 11
        y ^= (y << 7) & TEMPERING_MASK_A
        y ^= (y << 15) & TEMPERING_MASK_B
        y ^= (y >> 18)
        return intmask(y)

    def random(self):
        a = self.genrand32() >> 5
        b = self.genrand32() >> 6
        r = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)
        return r

    def randbelow(self, max = 0):
        a = self.genrand32() >> 5
        b = self.genrand32() >> 6
        if max == 0:
          r = (a * 67108864 + b)
        else:
          r = (a * 67108864 + b) % max
        return intmask(r)

    def randrange(self, start, stop=None, step=1):
        """Choose a random item from range(start, stop[, step]).

        This fixes the problem with randint() which includes the
        endpoint; in Python this is usually not what you want.

        Do not supply the 'int' argument.
        """

        # This code is a bit messy to make it fast for the
        # common case while still doing adequate error checking.
        if stop is None:
            if start > 0:
                return self.randbelow(start)
            raise ValueError("empty range for randrange()")

        width = stop - start
        if step == 1 and width > 0:
            return start + self.randbelow(width)
        if step == 1:
            raise ValueError("empty range for randrange() (%d,%d, %d)" % (start, stop, width))

        # Non-unit step argument supplied.
        if step > 0:
            n = (width + step - 1) / step
        elif step < 0:
            n = (width + step + 1) / step
        else:
            raise ValueError("zero step for randrange()")

        if n <= 0:
            raise ValueError("empty range for randrange()")

        return start + step * self.randbelow(n)

    def randint(self, a, b):
        """Return random integer in range [a, b], including both end points.
        """

        return self.randrange(a, b+1)
    
    def jumpahead(self, n):
        mt = self.state
        for i in range(N - 1, 0, -1):
            j = n % i
            mt[i], mt[j] = mt[j], mt[i]
        for i in range(N):
            mt[i] += r_uint(i + 1)
        self.index = N

    # The remainder of the code is taken primarily from:
    # http://svn.python.org/projects/python/branches/py3k/Lib/random.py
    

    # Translated by Guido van Rossum from C source provided by
    # Adrian Baddeley.  Adapted by Raymond Hettinger for use with
    # the Mersenne Twister  and os.urandom() core generators.

    ## -------------------- sequence methods  -------------------

    def choice(self, seq):
        """Choose a random element from a non-empty sequence."""
        try:
            i = self.randbelow(len(seq))
        except ValueError:
            raise IndexError('Cannot choose from an empty sequence')
        return seq[i]

    def shuffle(self, x):
        """x, random=random.random -> shuffle list x in place; return None.

        Optional arg random is a 0-argument function returning a random
        float in [0.0, 1.0); by default, the standard random.random.
        """

        for i in reversed(range(1, len(x))):
            # pick an element in x[:i+1] with which to exchange x[i]
            j = self.randbelow(i+1)
            x[i], x[j] = x[j], x[i]

## -------------------- real-valued distributions  -------------------

## -------------------- uniform distribution -------------------

    def uniform(self, a, b):
        "Get a random number in the range [a, b) or [a, b] depending on rounding."
        return a + (b-a) * self.random()

## -------------------- triangular --------------------

    def triangular(self, low=0.0, high=1.0, mode=None):
        """Triangular distribution.

        Continuous distribution bounded by given lower and upper limits,
        and having a given mode value in-between.

        http://en.wikipedia.org/wiki/Triangular_distribution

        """
        u = self.random()
        c = 0.5 if mode is None else (mode - low) / (0.0 + high - low)
        if u > c:
            u = 1.0 - u
            c = 1.0 - c
            low, high = high, low
        return low + (high - low) * math.pow(u * c, 0.5)

## -------------------- normal distribution --------------------

    def normalvariate(self, mu, sigma):
        """Normal distribution.

        mu is the mean, and sigma is the standard deviation.

        """
        # mu = mean, sigma = standard deviation

        # Uses Kinderman and Monahan method. Reference: Kinderman,
        # A.J. and Monahan, J.F., "Computer generation of random
        # variables using the ratio of uniform deviates", ACM Trans
        # Math Software, 3, (1977), pp257-260.

        while 1:
            u1 = self.random()
            u2 = 1.0 - self.random()
            z = NV_MAGICCONST*(u1-0.5)/u2
            zz = z*z/4.0
            if zz <= -math.log(u2):
                break
        return mu + z*sigma

## -------------------- lognormal distribution --------------------

    def lognormvariate(self, mu, sigma):
        """Log normal distribution.

        If you take the natural logarithm of this distribution, you'll get a
        normal distribution with mean mu and standard deviation sigma.
        mu can have any value, and sigma must be greater than zero.

        """
        return math.exp(self.normalvariate(mu, sigma))

## -------------------- exponential distribution --------------------

    def expovariate(self, lambd):
        """Exponential distribution.

        lambd is 1.0 divided by the desired mean.  It should be
        nonzero.  (The parameter would be called "lambda", but that is
        a reserved word in Python.)  Returned values range from 0 to
        positive infinity if lambd is positive, and from negative
        infinity to 0 if lambd is negative.

        """
        # lambd: rate lambd = 1/mean
        # ('lambda' is a Python reserved word)

        u = self.random()
        while u <= 1e-7:
            u = self.random()
        return -math.log(u)/(lambd)


## -------------------- von Mises distribution --------------------

    def vonmisesvariate(self, mu, kappa):
        """Circular data distribution.

        mu is the mean angle, expressed in radians between 0 and 2*pi, and
        kappa is the concentration parameter, which must be greater than or
        equal to zero.  If kappa is equal to zero, this distribution reduces
        to a uniform random angle over the range 0 to 2*pi.

        """
        # mu:    mean angle (in radians between 0 and 2*pi)
        # kappa: concentration parameter kappa (>= 0)
        # if kappa = 0 generate uniform random angle

        # Based upon an algorithm published in: Fisher, N.I.,
        # "Statistical Analysis of Circular Data", Cambridge
        # University Press, 1993.

        # Thanks to Magnus Kessler for a correction to the
        # implementation of step 4.

        if kappa <= 1e-6:
            return TWOPI * self.random()

        a = 1.0 + math.sqrt(1.0 + 4.0 * kappa * kappa)
        b = (a - math.sqrt(2.0 * a))/(2.0 * kappa)
        r = (1.0 + b * b)/(2.0 * b)

        while 1:
            u1 = self.random()

            z = math.cos(math.pi * u1)
            f = (1.0 + r * z)/(r + z)
            c = kappa * (r - f)

            u2 = self.random()

            if u2 < c * (2.0 - c) or u2 <= c * math.exp(1.0 - c):
                break

        u3 = self.random()
        if u3 > 0.5:
            theta = (mu % TWOPI) + math.acos(f)
        else:
            theta = (mu % TWOPI) - math.acos(f)

        return theta


## -------------------- gamma distribution --------------------

    def gammavariate(self, alpha, beta):
        
        """Gamma distribution.  Not the gamma function!

        Conditions on the parameters are alpha > 0 and beta > 0.

        """

        # alpha > 0, beta > 0, mean is alpha*beta, variance is alpha*beta**2

        # Warning: a few older sources define the gamma distribution in terms
        # of alpha > -1.0
        if alpha <= 0.0 or beta <= 0.0:
            raise ValueError('gammavariate: alpha and beta must be > 0.0')

        if alpha > 1.0:

            # Uses R.C.H. Cheng, "The generation of Gamma
            # variables with non-integral shape parameters",
            # Applied Statistics, (1977), 26, No. 1, p71-74

            ainv = math.sqrt(2.0 * alpha - 1.0)
            bbb = alpha - LOG4
            ccc = alpha + ainv

            while 1:
                u1 = self.random()
                if not 1e-7 < u1 < .9999999:
                    continue
                u2 = 1.0 - self.random()
                v = math.log(u1/(1.0-u1))/(ainv)
                x = alpha*math.exp(v)
                z = u1*u1*u2
                r = bbb+ccc*v-x
                if r + SG_MAGICCONST - 4.5*z >= 0.0 or r >= math.log(z):
                    return x * beta

        elif alpha == 1.0:
            # expovariate(1)
            u = self.random()
            while u <= 1e-7:
                u = self.random()
            return -math.log(u) * beta

        else:   # alpha is between 0 and 1 (exclusive)

            # Uses ALGORITHM GS of Statistical Computing - Kennedy & Gentle

            while 1:
                u = self.random()
                b = (math.e + alpha)/math.e
                p = b*u
                if p <= 1.0:
                    x = math.pow(p, (1.0/alpha))
                else:
                    x = -math.log((b-p)/(alpha))
                u1 = self.random()
                if p > 1.0:
                    if u1 <= math.pow(x, alpha - 1.0):
                        break
                elif u1 <= math.exp(-x):
                    break
            return x * beta

## -------------------- Gauss (faster alternative) --------------------

    def gauss(self, mu, sigma):
        """Gaussian distribution.

        mu is the mean, and sigma is the standard deviation.  This is
        slightly faster than the normalvariate() function.

        Not thread-safe without a lock around calls.

        """

        # When x and y are two variables from [0, 1), uniformly
        # distributed, then
        #
        #    cos(2*pi*x)*sqrt(-2*log(1-y))
        #    sin(2*pi*x)*sqrt(-2*log(1-y))
        #
        # are two *independent* variables with normal distribution
        # (mu = 0, sigma = 1).
        # (Lambert Meertens)
        # (corrected version; bug discovered by Mike Miller, fixed by LM)

        # Multithreading note: When two threads call this function
        # simultaneously, it is possible that they will receive the
        # same return value.  The window is very small though.  To
        # avoid this, you have to use a lock around all calls.  (I
        # didn't want to slow this down in the serial case by using a
        # lock here.)

        z = self.gauss_next
        self.gauss_next = None
        if z is None:
            x2pi = self.random() * TWOPI
            g2rad = math.sqrt(-2.0 * math.log(1.0 - self.random()))
            z = math.cos(x2pi) * g2rad
            self.gauss_next = math.sin(x2pi) * g2rad

        return mu + z*sigma

## -------------------- beta --------------------
## See
## http://sourceforge.net/bugs/?func=detailbug&bug_id=130030&group_id=5470
## for Ivan Frohne's insightful analysis of why the original implementation:
##
##    def betavariate(self, alpha, beta):
##        # Discrete Event Simulation in C, pp 87-88.
##
##        y = self.expovariate(alpha)
##        z = self.expovariate(1.0/beta)
##        return z/(y+z)
##
## was dead wrong, and how it probably got that way.

    def betavariate(self, alpha, beta):
        """Beta distribution.

        Conditions on the parameters are alpha > 0 and beta > 0.
        Returned values range between 0 and 1.

        """

        # This version due to Janne Sinkkonen, and matches all the std
        # texts (e.g., Knuth Vol 2 Ed 3 pg 134 "the beta distribution").
        y = self.gammavariate(alpha, 1.)
        if y == 0:
            return 0.0
        else:
            return y / (y + self.gammavariate(beta, 1.))

## -------------------- Pareto --------------------

    def paretovariate(self, alpha):
        """Pareto distribution.  alpha is the shape parameter."""
        # Jain, pg. 495

        u = 1.0 - self.random()
        return 1.0 / math.pow(u, (1.0/alpha))

## -------------------- Weibull --------------------

    def weibullvariate(self, alpha, beta):
        """Weibull distribution.

        alpha is the scale parameter and beta is the shape parameter.

        """
        # Jain, pg. 499; bug fix courtesy Bill Arms

        u = 1.0 - self.random()
        return alpha * math.pow(-math.log(u), (1.0/beta))


random = Random()

