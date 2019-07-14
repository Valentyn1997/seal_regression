import seal
from seal import ChooserEvaluator, \
    Ciphertext, \
    Decryptor, \
    Encryptor, \
    EncryptionParameters, \
    Evaluator, \
    FractionalEncoder, \
    KeyGenerator, \
    Plaintext, \
    SEALContext


class FracContext:
    def __init__(self):
        self.params = EncryptionParameters()
        self.params.set_poly_modulus("1x^2048 + 1")
        self.params.set_coeff_modulus(seal.coeff_modulus_128(2048))
        self.params.set_plain_modulus(1 << 8)

        self.context = SEALContext(self.params)
        self.print_parameters(self.context)

        self.keygen = KeyGenerator(self.context)
        self.public_key = self.keygen.public_key()
        self.secret_key = self.keygen.secret_key()
        self.evaluator = Evaluator(self.context)

    def print_parameters(self, context):
        print("/ Encryption parameters:")
        print("| poly_modulus: " + context.poly_modulus().to_string())

        # Print the size of the true (product) coefficient modulus
        print("| coeff_modulus_size: " + (str)(context.total_coeff_modulus().significant_bit_count()) + " bits")

        print("| plain_modulus: " + (str)(context.plain_modulus().value()))
        print("| noise_standard_deviation: " + (str)(context.noise_standard_deviation()))


class FractionalDecoderUtils:
    def __init__(self, context):
        self.context = context.context
        self.secret_key = context.secret_key
        self.decryptor = Decryptor(self.context, self.secret_key)
        self.encoder = FractionalEncoder(self.context.plain_modulus(),
                                         self.context.poly_modulus(),
                                         64, 32, 3)
        self.evaluator = context.evaluator

    def decode(self, encrypted_res):
        plain_result = Plaintext()
        self.decryptor.decrypt(encrypted_res, plain_result)
        result = self.encoder.decode(plain_result)
        return result


class FractionalEncoderUtils:
    def __init__(self, context):
        self.context = context.context
        self.public_key = context.public_key
        self.encryptor = Encryptor(self.context, self.public_key)
        self.encoder = FractionalEncoder(self.context.plain_modulus(),
                                         self.context.poly_modulus(),
                                         64, 32, 3)
        self.evaluator = context.evaluator

    def encode_rationals(self, numbers):
        # encoding without encryption
        encoded_coefficients = []
        for i in range(len(numbers)):
            encoded_coefficients.append(self.encoder.encode(numbers[i]))
        return encoded_coefficients

    def encode_num(self, num):
        # encoding without encryption
        return self.encoder.encode(num)

    def sum_enc_array(self, array):
        encrypted_result = Ciphertext()
        self.evaluator.add_many(array, encrypted_result)
        return encrypted_result

    def encrypt_rationals(self, rational_numbers):
        """
        :param rational_numbers: array of rational numbers
        :return: encrypted result
        """
        encrypted_rationals = []
        for i in range(len(rational_numbers)):
            encrypted_rationals.append(Ciphertext(self.context.params))
            self.encryptor.encrypt(self.encoder.encode(rational_numbers[i]), encrypted_rationals[i])
        return encrypted_rationals

    def weighted_average(self, encrypted_rationals, encoded_coefficients, encoded_divide_by):

        for i in range(len(encrypted_rationals)):
            self.evaluator.multiply_plain(encrypted_rationals[i], encoded_coefficients[i])

        encrypted_result = Ciphertext()
        self.evaluator.add_many(encrypted_rationals, encrypted_result)
        self.evaluator.multiply_plain(encrypted_result, encoded_divide_by)

        return encrypted_result

    def substract(self, a, b):
        """
        :param a: encrypted fractional value
        :param b: encrypted fractional value
        :return: substracted result
        """
        minus_sign = self.encoder.encode(-1)
        self.evaluator.multiply_plain(b, minus_sign)
        self.evaluator.add(a, b)
        return a

    def encrypt_num(self, value):
        plain = self.encoder.encode(value)
        encrypted = Ciphertext()
        self.encryptor.encrypt(plain, encrypted)
        return encrypted

    def add(self, a, b):
        """
        :param a: encrypted fractional value
        :param b: encrypted fractional value
        :return: sum
        """
        self.evaluator.add(a, b)
        return a

    def multiply(self, a, b):
        self.evaluator.multiply(a, b)
        return a
