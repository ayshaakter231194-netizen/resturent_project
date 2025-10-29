from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from io import BytesIO
from .models import Category, FoodItem, Customer, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'created')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'city', 'address')
    search_fields = ('name', 'phone', 'address')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('food', 'quantity', 'price_at_order')
    extra = 0
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'created_at', 'total_amount_display', 'location_display', 'status_display', 'invoice_actions')
    list_filter = ('inside_dhaka', 'is_completed', 'created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'order_summary', 'invoice_preview', 'customer_address_display')
    fieldsets = (
        ('Order Information', {
            'fields': ('customer', 'created_at', 'is_completed')
        }),
        ('Customer Information', {
            'fields': ('customer_address_display',)
        }),
        ('Delivery Information', {
            'fields': ('inside_dhaka', 'payment_method', 'note')
        }),
        ('Financial Details', {
            'fields': ('total', 'delivery_fee')
        }),
        ('Order Summary', {
            'fields': ('order_summary',)
        }),
        ('Invoice', {
            'fields': ('invoice_preview',)
        })
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/invoice/', self.admin_site.admin_view(self.generate_invoice), name='order_invoice'),
            path('<path:object_id>/receipt/', self.admin_site.admin_view(self.generate_receipt), name='order_receipt'),
        ]
        return custom_urls + urls
    
    def total_amount_display(self, obj):
        return f"Tk. {obj.total}"
    total_amount_display.short_description = 'Total Amount'
    
    def location_display(self, obj):
        if obj.inside_dhaka:
            return "Inside Dhaka"
        return "Outside Dhaka"
    location_display.short_description = 'Location'
    
    def status_display(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green;">✓ Completed</span>')
        return format_html('<span style="color: orange;">● Pending</span>')
    status_display.short_description = 'Status'
    
    def customer_address_display(self, obj):
        """Display customer address in order details"""
        if obj.customer.address:
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 5px 0;">'
                '<strong>Address:</strong> {}<br>'
                '<strong>City:</strong> {}<br>'
                '<strong>Phone:</strong> {}'
                '</div>',
                obj.customer.address,
                obj.customer.city,
                obj.customer.phone
            )
        else:
            return format_html(
                '<div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin: 5px 0;">'
                '<strong>City:</strong> {}<br>'
                '<strong>Phone:</strong> {}<br>'
                '<em>No address provided</em>'
                '</div>',
                obj.customer.city,
                obj.customer.phone
            )
    customer_address_display.short_description = 'Customer Address & Contact'
    
    def invoice_actions(self, obj):
        return format_html(
            '<div style="display: flex; gap: 5px; flex-wrap: wrap;">'
            '<a class="button" href="{}" style="background: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;" target="_blank">Invoice</a>'
            '<a class="button" href="{}" style="background: #2196F3; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;" target="_blank">POS Receipt</a>'
            '</div>',
            f'{obj.id}/invoice/',
            f'{obj.id}/receipt/'
        )
    invoice_actions.short_description = 'Actions'
    
    def order_summary(self, obj):
        items = obj.items.all()
        summary = []
        for item in items:
            summary.append(f"{item.quantity} x {item.food.name} - Tk. {item.price_at_order} each")
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">'
            '<strong>Order Items:</strong><br>'
            '{}<br>'
            '<strong>Subtotal:</strong> Tk. {}<br>'
            '<strong>Delivery Fee:</strong> Tk. {}<br>'
            '<strong>Total:</strong> Tk. {}'
            '</div>',
            '<br>'.join(summary),
            obj.total - obj.delivery_fee,
            obj.delivery_fee,
            obj.total
        )
    order_summary.short_description = 'Order Summary'
    
    def invoice_preview(self, obj):
        return format_html(
            '<div style="text-align: center; margin: 20px 0;">'
            '<a href="{}" class="button" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;" target="_blank">View Full Invoice</a>'
            '<a href="{}" class="button" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;" target="_blank">Print POS Receipt</a>'
            '</div>',
            f'{obj.id}/invoice/',
            f'{obj.id}/receipt/'
        )
    invoice_preview.short_description = 'Invoice & Receipt'
    
    def _get_order_id(self, object_id):
        """Extract the actual order ID from the object_id parameter"""
        if '/' in object_id:
            return object_id.split('/')[0]
        return object_id
    
    def generate_invoice(self, request, object_id):
        order_id = self._get_order_id(object_id)
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            from django.http import Http404
            raise Http404(f"Order with id {order_id} does not exist")
        
        items = order.items.all()
        subtotal = order.total - order.delivery_fee
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
        
        # Create PDF document
        doc = SimpleDocTemplate(response, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center
        )
        elements.append(Paragraph('TASTYBITE RESTAURANT', title_style))
        
        # Restaurant info
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            spaceAfter=20,
        )
        elements.append(Paragraph('123 Food Street, Gulshan, Dhaka 1212<br/>Phone: +880 1234-567890<br/>Invoice #: ' + str(order.id), info_style))
        
        # Customer Information
        elements.append(Paragraph('Customer Information', styles['Heading2']))
        customer_data = [
            ['Name:', order.customer.name],
            ['Phone:', order.customer.phone],
            ['Address:', order.customer.address or 'Not provided'],
            ['City:', order.customer.city],
        ]
        customer_table = Table(customer_data, colWidths=[1.5*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Order Information
        elements.append(Paragraph('Order Information', styles['Heading2']))
        order_data = [
            ['Order Date:', order.created_at.strftime("%B %d, %Y %H:%M")],
            ['Location:', 'Inside Dhaka' if order.inside_dhaka else 'Outside Dhaka'],
            ['Payment Method:', order.get_payment_method_display()],
            ['Status:', 'Completed' if order.is_completed else 'Pending'],
        ]
        order_table = Table(order_data, colWidths=[1.5*inch, 4*inch])
        order_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(order_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Order Items
        elements.append(Paragraph('Order Items', styles['Heading2']))
        items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
        for item in items:
            items_data.append([
                item.food.name,
                str(item.quantity),
                f'Tk. {item.price_at_order}',
                f'Tk. {item.quantity * item.price_at_order}'
            ])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Totals
        totals_data = [
            ['Subtotal:', f'Tk. {subtotal}'],
            ['Delivery Fee:', f'Tk. {order.delivery_fee}'],
            ['Grand Total:', f'Tk. {order.total}']
        ]
        totals_table = Table(totals_data, colWidths=[4*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
            ('FONT', (-1, -1), (-1, -1), 'Helvetica-Bold', 14),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('LINEABOVE', (-1, -1), (-1, -1), 2, colors.black),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(totals_table)
        
        # Note
        if order.note:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph('Order Note', styles['Heading3']))
            elements.append(Paragraph(order.note, styles['Normal']))
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.grey,
        )
        elements.append(Paragraph('Thank you for your order!<br/>TastyBite Restaurant - Delicious Food Delivered', footer_style))
        
        # Build PDF
        doc.build(elements)
        return response
    
    def generate_receipt(self, request, object_id):
        order_id = self._get_order_id(object_id)
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            from django.http import Http404
            raise Http404(f"Order with id {order_id} does not exist")
        
        items = order.items.all()
        subtotal = order.total - order.delivery_fee
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{order.id}.pdf"'
        
        # Create PDF with POS size (80mm width)
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(80*mm, 200*mm))
        width, height = 80*mm, 200*mm
        
        # Header
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, height-20, "TASTYBITE")
        p.setFont("Helvetica", 8)
        p.drawCentredString(width/2, height-30, "123 Food Street, Gulshan")
        p.drawCentredString(width/2, height-40, "Phone: +880 1234-567890")
        
        # Order info
        p.drawCentredString(width/2, height-50, f"Order #: {order.id}")
        p.drawCentredString(width/2, height-60, order.created_at.strftime("%d/%m/%Y %H:%M"))
        
        # Divider
        p.line(10, height-65, width-10, height-65)
        
        # Customer info
        y_position = height - 75
        p.setFont("Helvetica-Bold", 9)
        p.drawString(10, y_position, "CUSTOMER")
        p.setFont("Helvetica", 8)
        y_position -= 12
        p.drawString(10, y_position, order.customer.name)
        y_position -= 10
        p.drawString(10, y_position, order.customer.phone)
        y_position -= 10
        
        # Address handling
        if order.customer.address:
            # Split address into multiple lines if too long
            address_lines = []
            current_line = ""
            for word in order.customer.address.split():
                if len(current_line + " " + word) <= 35:
                    current_line += " " + word
                else:
                    address_lines.append(current_line.strip())
                    current_line = word
            if current_line:
                address_lines.append(current_line.strip())
            
            for line in address_lines:
                p.drawString(10, y_position, line)
                y_position -= 10
        else:
            p.drawString(10, y_position, "Address: Not provided")
            y_position -= 10
        
        p.drawString(10, y_position, f"City: {order.customer.city}")
        y_position -= 15
        
        # Divider
        p.line(10, y_position, width-10, y_position)
        y_position -= 10
        
        # Order items
        p.setFont("Helvetica-Bold", 9)
        p.drawString(10, y_position, "ORDER ITEMS")
        y_position -= 15
        
        p.setFont("Helvetica", 8)
        for item in items:
            # Item name and quantity
            item_line = f"{item.quantity}x {item.food.name}"
            p.drawString(10, y_position, item_line[:35])  # Limit to 35 chars
            y_position -= 8
            
            # Price - Using Tk. instead of ৳
            item_total = item.quantity * item.price_at_order
            price_line = f"@ Tk. {item.price_at_order} each"
            p.drawString(10, y_position, price_line)
            p.drawRightString(width-10, y_position, f"Tk. {item_total}")
            y_position -= 12
        
        # Double divider
        p.setLineWidth(2)
        p.line(10, y_position, width-10, y_position)
        y_position -= 10
        p.setLineWidth(1)
        
        # Totals - Using Tk. instead of ৳
        p.setFont("Helvetica", 9)
        p.drawString(10, y_position, "Subtotal:")
        p.drawRightString(width-10, y_position, f"Tk. {subtotal}")
        y_position -= 12
        
        p.drawString(10, y_position, "Delivery Fee:")
        p.drawRightString(width-10, y_position, f"Tk. {order.delivery_fee}")
        y_position -= 15
        
        p.setFont("Helvetica-Bold", 10)
        p.drawString(10, y_position, "TOTAL:")
        p.drawRightString(width-10, y_position, f"Tk. {order.total}")
        y_position -= 20
        
        # Divider
        p.line(10, y_position, width-10, y_position)
        y_position -= 10
        
        # Payment info
        p.setFont("Helvetica-Bold", 9)
        p.drawString(10, y_position, "PAYMENT")
        p.setFont("Helvetica", 8)
        y_position -= 10
        p.drawString(10, y_position, f"Method: {order.get_payment_method_display()}")
        y_position -= 10
        location = "Inside Dhaka" if order.inside_dhaka else "Outside Dhaka"
        p.drawString(10, y_position, f"Location: {location}")
        y_position -= 15
        
        # Note
        if order.note:
            p.line(10, y_position, width-10, y_position)
            y_position -= 10
            p.setFont("Helvetica-Bold", 9)
            p.drawString(10, y_position, "NOTE")
            p.setFont("Helvetica", 8)
            y_position -= 10
            # Split note into multiple lines
            note_lines = []
            current_line = ""
            for word in order.note.split():
                if len(current_line + " " + word) <= 35:
                    current_line += " " + word
                else:
                    note_lines.append(current_line.strip())
                    current_line = word
            if current_line:
                note_lines.append(current_line.strip())
            
            for line in note_lines:
                p.drawString(10, y_position, line)
                y_position -= 10
        
        # Double divider
        p.setLineWidth(2)
        p.line(10, y_position, width-10, y_position)
        y_position -= 15
        
        # Footer
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(width/2, y_position, "Thank you for your order!")
        y_position -= 10
        p.drawCentredString(width/2, y_position, "** TastyBite Restaurant **")
        
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response