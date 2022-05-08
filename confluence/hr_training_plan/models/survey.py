
import re

from odoo import api, exceptions, fields, models, tools, _
from odoo.exceptions import AccessError, UserError

emails_split = re.compile(r"[;,\n\r]+")

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'
    training_id = fields.Many2one('hr.training.execution')


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    training_id = fields.Many2one('hr.training.execution')
    def action_invite(self):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed """
        self.ensure_one()
        Partner = self.env['res.partner']

        # compute partners and emails, try to find partners for given emails
        valid_partners = self.partner_ids
        valid_emails = []
        for email in emails_split.split(self.emails or ''):
            partner = False
            email_normalized = tools.email_normalize(email)
            if email_normalized:
                limit = None if self.survey_users_login_required else 1
                partner = Partner.search([('email_normalized', '=', email_normalized)], limit=limit)
            if partner:
                valid_partners |= partner
            else:
                email_formatted = tools.email_split_and_format(email)
                if email_formatted:
                    valid_emails.extend(email_formatted)

        if not valid_partners and not valid_emails:
            raise UserError(_("Please enter at least one valid recipient."))

        answers = self._prepare_answers(valid_partners, valid_emails)
        answers.sudo().write({'training_id': self.training_id.id})
        for answer in answers:
            self._send_mail(answer)

        return {'type': 'ir.actions.act_window_close'}


