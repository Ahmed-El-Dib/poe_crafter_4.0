from config import *
from macros.currency_macros import spam_currency, use_currency, alt_currency


class CurrencyManager:
    def __init__(
        self,
        max_alts=5000,
        max_exalts=590,
        max_scoures=1400,
        max_regals=1680,
        max_annuls=60,
        max_augments=999999,
        max_transmutes=999999,
    ):
        self.spamming = False

        # usage counters
        self.alts = 0
        self.exalts = 0
        self.scoures = 0
        self.regals = 0
        self.annuls = 0
        self.augments = 0
        self.transmutes = 0

        # limits
        self.max_alts = max_alts
        self.max_exalts = max_exalts
        self.max_scoures = max_scoures
        self.max_regals = max_regals
        self.max_annuls = max_annuls
        self.max_augments = max_augments
        self.max_transmutes = max_transmutes

    # ---------- internal helper ----------
    def _check(self, current, maximum, name):
        if current >= maximum:
            print(f"{name} limit reached, exiting.")
            exit()

    # ---------- currency actions ----------
    def trans(self):
        self._check(self.transmutes, self.max_transmutes, "Transmute")
        self.transmutes += 1
        self.stop_spamming()
        use_currency(TRANS, spammable=False)
    
    def alt(self):
        self._check(self.alts, self.max_alts, "Alt")
        self.alts += 1
        alt_loc = self.check_alt_location()
        if self.spamming:
            spam_currency(alt_loc)
        else:
            self.spamming = True
            use_currency(alt_loc, spammable=True)

    def aug(self):
        self._check(self.augments, self.max_augments, "Augment")
        self.augments += 1
        if self.spamming:
            alt_currency(AUG)
        else:
            self.stop_spamming()
            use_currency(AUG, spammable=False)

    def slam(self):
        self._check(self.exalts, self.max_exalts, "Exalt")
        self.exalts += 1
        use_currency(EXALT)

    def scoure(self):
        self._check(self.scoures, self.max_scoures, "Scoure")
        self.scoures += 1
        self.stop_spamming()
        use_currency(SCOURE, spammable=False)

    def annul(self):
        self._check(self.annuls, self.max_annuls, "Annul")
        self.annuls += 1
        self.stop_spamming()
        use_currency(ANNUL, spammable=False)

    def regal(self):
        self._check(self.regals, self.max_regals, "Regal")
        self.regals += 1
        self.stop_spamming()
        use_currency(REGAL, spammable=False)


    # ---------- utility ----------
    def stop_spamming(self):
        self.spamming = False

    def check_alt_location(self):
        if self.alts < 4950:
            return ALT
        elif self.alts < 4950*2:
            return ALT_2
        else:
            return ALT_3