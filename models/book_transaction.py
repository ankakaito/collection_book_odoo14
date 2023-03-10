from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class BookTransactionLine(models.Model):
    _name = 'book.transaction.line'
    _description = 'Book Transaction Line'

    management_id = fields.Many2one('book.management','Book Title')
    transaction_id = fields.Many2one('book.transaction', 'Transaction ID')
    #book_title = fields.Char('Book Title')
    qty = fields.Integer(string='Qty')

    # @api.onchange('management_id')
    # def onchange_management_id(self):
    #     for rec in self:
    #         if rec.management_id:
    #             rec.book_title = rec.management_id.book_id.name

    def get_excel_report(self):

        return {
            'type': 'ir.actions.act_url',
            'url': '/collection_book/book_transaction_report_excel/%s' % (self.id),
            'target': 'new',
        }

    @api.constrains('qty')
    def check_val_qty(self):
        for rec in self:
            if rec.qty < 0:
                raise ValidationError('Qty Input must more or less then 0')

    @api.constrains('qty')
    def check_val_qty(self):
        for rec in self:
            if rec.qty == 0:
                raise ValidationError('Qty must more than 0')

class BookTransaction(models.Model):
    _name = 'book.transaction'
    _description = 'Book Transaction'


    def func_to_approve(self):
        if self.status == 'draft':
            if len(self.transaction_ids) == 0:
                raise ValidationError('Please Fill The Transaction Line Before Settle to Approve')
            else:
                self.status = 'to_approve'
                self.validation = "processing"
    def func_approved(self):
        if self.status == 'to_approve':
            if len(self.transaction_ids) == 0:
                raise ValidationError('Please Fill The Transaction Line Before Settle to Approve')
            else:
                self.status = 'approved'
                self.validation = "processing"

    def func_done(self):
        if self.status == 'approved':
            if len(self.transaction_ids) == 0:
                raise ValidationError('Please Fill The Transaction Line Before Settle to Approve')
            else:
                if len(self.transaction_ids) > 0:
                    for transaction in self.transaction_ids:
                        total_qty = transaction.management_id.book_qty - transaction.management_id.amount_borrowed
                        #if transaction.management_id.amount_borrowed >= transaction.qty:
                        if transaction.qty > total_qty:
                            #raise ValidationError(' The number your Book Is Out Of Stok Please Choose Another Book ')
                            raise ValidationError(_( "Your Stock is %s Book %s, Your book request is out of Stok, Please Choose Another Book" % (total_qty, transaction.management_id.book_id.name)))
                        else:
                            transaction.management_id.write({'amount_borrowed': total_qty})
                            self.status = 'done'
                            self.validation = 'borrowed'
                        #transaction.management_id.write({'amount_borrowed': 0})

   # def get_excel_report(self):
   #     return {
   #          'type': 'ir.actions.act_url',
   #          'url': '/collection_book/book_transaction_report_execl/%s' % (self.id),
   #          'target': 'new',
   #     }

    #@api.multi
    def get_excel_report(self):
        return self.env.ref('collection_book.report_master_transaction_views').report_action(self)

    name = fields.Char(string="Transaction Number", default='New')
    member_id = fields.Many2one('member',"Member Name")
    borrowing_date = fields.Date(string="Borrowing Date", default=fields.Date.today())
    returning_date= fields.Datetime(string="Returning Date")
    transaction_ids = fields.One2many('book.transaction.line','transaction_id',"List Book Management", ondelete='cascade')
    status = fields.Selection([('draft','Draft'),('to_approve','To Approve'),('approved','Approved'),('done','Done')], default='draft')
    validation = fields.Selection([('processing','Processing'),('borrowed','Borrowed'),('returned','Returned')], string="Transaction Status",  default='processing')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'seq.book.transaction') or 'New'
        result = super(BookTransaction, self).create(vals)
        return result
    
    @api.onchange('transaction_ids')
    def _onchange_management_id(self):
        for rec in self:
            for line in rec.transaction_ids:
                check_line = self._check_duplicate_ids(rec.transaction_ids, line.management_id.id, line.id)
                if check_line:
                    raise ValidationError('Cant duplicate book')
    
    def _check_duplicate_ids(self, line_ids, management_id, id):
        for line in line_ids:
            if line.management_id.id == management_id and line.id != id:
                return True
        return False
