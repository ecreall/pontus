# -*- coding: utf-8 -*-
# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi


"""Default user-facing error messages (French-authored) used by
``ViewError`` renderings across views and operations.
"""
IndexViewErrorPrincipalmessage = u"Vous n'avez pas les droits suffisants pour accéder à l'information demandée."
IndexViewErrorCauses = [u"Vous ne disposez pas des rôles nécessaires.",
                        u"Certaines conditions ne sont pas encore satisfaites."]
IndexViewErrorSolutions = [u"Contactez l'administrateur..."]

MultipleViewErrorPrincipalmessage = u"Vous n'avez pas les droits suffisants pour accéder à l'ensemble des informations demandées."
MultipleViewErrorCauses = [u"Vous ne disposez pas des rôles nécessaires.",
                            u"Certaines conditions ne sont pas encore satisfaites."]
MultipleViewErrorSolutions = [u"Contactez l'administrateur..."]

CallViewErrorPrincipalmessage = u"Vous n'avez pas les droits suffisants pour appliquer l'action suivante aux informations demandées."
CallViewErrorCildrenNotValidatedmessage = u"Certaines informations n'ont pas été prises en compte!"
CallViewViewErrorCauses =  [u"Vous ne disposez pas des rôles nécessaires.",
                            u"Certaines conditions ne sont pas encore satisfaites."]


BehaviorViewErrorPrincipalmessage = u"Vous n'avez pas les droits suffisants pour réaliser l'action demandée."
BehaviorViewErrorCauses = [u"Vous ne disposez pas des rôles nécessaires.",
                        u"Certaines conditions ne sont pas encore satisfaites.",
                        u"L'action est vérouiée par un autre utilisateur."]
BehaviorViewErrorSolutions = [u"Contactez l'administrateur..."]

# Backward-compatibility aliases (historical typos, renamed 2026-07-17)
MutltipleViewErrorPrincipalmessage = MultipleViewErrorPrincipalmessage
MutltipleViewErrorCauses = MultipleViewErrorCauses
MutltipleViewErrorSolutions = MultipleViewErrorSolutions
