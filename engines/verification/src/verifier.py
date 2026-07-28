class Verifier:

    def verify(self, result):
        if result is None:
            return False

        if isinstance(result, str) and result.strip() == "":
            return False

        return True
