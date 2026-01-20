from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import *
from decimal import Decimal, InvalidOperation
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.core.paginator import Paginator
from datetime import *


def is_admin(user):
    """Check if user is in the 'admins' group or is a superuser."""
    return user.is_superuser or user.groups.filter(name='admins').exists()


def index(request):
    """Redirect to sales page (requires login)."""
    return redirect('sales')


@login_required
def operations_list(request):
    user_is_admin = is_admin(request.user)

    if request.method == "POST" and user_is_admin:
        action = request.POST.get("action")

        if action == "edit_operation":
            operation_id = request.POST.get("operation_id")
            operation = Operation.objects.filter(id=operation_id).first()
            if operation:
                # Build changes string
                changes_list = []
                original_author = operation.author
                initially_created = operation.created_at

                # Get new values
                new_type = request.POST.get("type", "").strip()
                new_sum_raw = request.POST.get("sum", "").strip()
                new_client_id = request.POST.get("client") or None
                new_product_id = request.POST.get("product") or None
                new_quantity_raw = request.POST.get("quantity", "").strip()
                new_comments = request.POST.get("comments", "").strip()
                new_date_raw = request.POST.get("date", "").strip()
                new_is_debt = request.POST.get("isDebt") == "on"

                # Parse new values
                try:
                    new_sum = Decimal(new_sum_raw) if new_sum_raw else operation.sum
                except (InvalidOperation, TypeError):
                    new_sum = operation.sum

                try:
                    new_quantity = int(new_quantity_raw) if new_quantity_raw else None
                except (ValueError, TypeError):
                    new_quantity = operation.quantity

                new_client = Client.objects.filter(id=new_client_id).first() if new_client_id else None
                new_product = Product.objects.filter(id=new_product_id).first() if new_product_id else None

                try:
                    new_date = datetime.strptime(new_date_raw, "%Y-%m-%d") if new_date_raw else operation.created_at
                except ValueError:
                    new_date = operation.created_at

                # Track changes
                if new_type and new_type != operation.type:
                    changes_list.append(f"type:'{operation.type}'->'{new_type}'")
                    operation.type = new_type

                if new_sum != operation.sum:
                    # Update balance if sum changed
                    balance = CurrentBalance.objects.first()
                    if operation.isDebt:
                        balance.debt -= operation.sum
                        balance.debt += new_sum
                    else:
                        balance.amount -= operation.sum
                        balance.amount += new_sum
                    balance.save()
                    changes_list.append(f"sum:'{operation.sum}'->'{new_sum}'")
                    operation.sum = new_sum

                old_client_name = f"{operation.client.status} {operation.client.firstname} {operation.client.lastname}" if operation.client else "None"
                new_client_name = f"{new_client.status} {new_client.firstname} {new_client.lastname}" if new_client else "None"
                if new_client != operation.client:
                    changes_list.append(f"client:'{old_client_name}'->'{new_client_name}'")
                    operation.client = new_client

                old_product_name = operation.product.name if operation.product else "None"
                new_product_name = new_product.name if new_product else "None"
                if new_product != operation.product:
                    changes_list.append(f"product:'{old_product_name}'->'{new_product_name}'")
                    operation.product = new_product

                if new_quantity != operation.quantity:
                    changes_list.append(f"quantity:'{operation.quantity}'->'{new_quantity}'")
                    operation.quantity = new_quantity

                if new_is_debt != operation.isDebt:
                    # Update balance when debt status changes
                    balance = CurrentBalance.objects.first()
                    if new_is_debt:
                        # Changed from paid to debt
                        balance.amount -= operation.sum
                        balance.debt += operation.sum
                    else:
                        # Changed from debt to paid
                        balance.debt -= operation.sum
                        balance.amount += operation.sum
                    balance.save()
                    changes_list.append(f"isDebt:'{operation.isDebt}'->'{new_is_debt}'")
                    operation.isDebt = new_is_debt

                if new_comments != (operation.comments or ""):
                    changes_list.append(f"comments:'{operation.comments or ''}'->'{new_comments}'")
                    operation.comments = new_comments if new_comments else None

                if new_date.date() != operation.created_at.date():
                    changes_list.append(f"date:'{operation.created_at.strftime('%Y-%m-%d')}'->'{new_date.strftime('%Y-%m-%d')}'")
                    operation.created_at = new_date

                # Save operation and create change record if there were changes
                if changes_list:
                    operation.save()
                    OperationChange.objects.create(
                        operation=operation,
                        initially_created=initially_created,
                        original_author=original_author,
                        edited_by=request.user,
                        changes=";".join(changes_list)
                    )

            return redirect('operations_list')

        else:
            # Default action: add new operation
            # read form data
            op_type = request.POST.get("type", "").strip()
            sum_raw = request.POST.get("sum", "").strip()
            client_id = request.POST.get("client") or None
            client_new = request.POST.get("client_new", "").strip()
            product_id = int(request.POST.get("product").split('-')[0]) or None
            quantity_raw = request.POST.get("quantity", "").strip()
            comments = request.POST.get("comments", "").strip() or None

            date = request.POST.get('date') if request.POST.get('date') != '' else datetime.now()


            # parse numeric fields
            try:
                sum_val = Decimal(sum_raw) if sum_raw != "" else Decimal("0.00")
            except (InvalidOperation, TypeError):
                sum_val = Decimal("0.00")

            try:
                quantity = int(quantity_raw) if quantity_raw != "" else None
            except (ValueError, TypeError):
                quantity = None

            # resolve/create client: client_new preferred
            client = None

            if client_new:

                parts = client_new.split(' ')
                status = parts[0] if len(parts) >= 1 else ""
                firstname = parts[1] if len(parts) >= 2 else ""
                lastname = " ".join(parts[2:]) if len(parts) >= 3 else ""
                client = Client.objects.create(status=status, firstname=firstname, lastname=lastname)
                client.save()

            else:
                client = Client.objects.filter(id=client_id).first() if client_id else None


            product = Product.objects.filter(id=product_id).first() if product_id else None

            balance = CurrentBalance.objects.first()

            if(request.POST.get('isDebt') != 'on'):
                balance.amount += sum_val

            else:
                balance.debt += sum_val
            balance.save()

            Operation.objects.create(
                type=op_type,
                sum=sum_val,
                client=client,
                product=product,
                quantity=quantity,
                comments=comments,
                isDebt = request.POST.get('isDebt') == 'on',
                created_at = date,
                author=request.user
            )

            # redirect to avoid resubmission (optional)
            return redirect(request.path)
    filters = {}
	# GET: fetch data for table and form
    if request.GET.get('client') != None:
    
        if request.GET.get('client') != '':
          
            filters['client_id'] = int(request.GET.get('client'))
        if request.GET.get('operation') != '':
            filters['type'] = request.GET.get('operation')
        if request.GET.get('date_from') != '':
            start_date = datetime.strptime(request.GET.get('date_from'), "%Y-%m-%d").date()
            filters['created_at__gte'] = start_date
        if request.GET.get('date_to') != '':
            end_date = datetime.strptime(request.GET.get('date_to'), "%Y-%m-%d").date()
            filters['created_at__lte'] = end_date
        if request.GET.get('sum_from') != '':
            filters['sum__gte'] = float(request.GET.get('sum_from'))
        if request.GET.get('sum_to') != '':
            filters['sum__lte'] = float(request.GET.get('sum_to'))


    operations = Operation.objects.filter(**filters).order_by('-id')
    paginator = Paginator(operations, 25) 
    page_number = request.GET.get("page")
    
    page_obj = paginator.get_page(page_number)
    clients = Client.objects.all().order_by('lastname', 'firstname')
    products = Product.objects.all().order_by('name')
    return render(request, 'register/operations_list.html', {
		'page_obj': page_obj,
		'clients': clients,
		'products': products,
        'types': OperationType.objects.all().order_by('id'),
        'balance': CurrentBalance.objects.first(),
        'is_admin': user_is_admin,
})


@login_required
def statistics(request):
    start_date = None
    end_date = datetime.now()
    labels = []

    if request.GET.get('period') == 'year':
        start_date = end_date.replace(month = 1, day=1)
    elif request.GET.get('from') != None:
        start_date = datetime.strptime(request.GET.get('from'), "%Y-%m-%d").date()
        end_date = datetime.strptime(request.GET.get('to'), "%Y-%m-%d").date()
    else:
        start_date = end_date.replace(day = 1)
    

    dt = end_date - start_date
    if dt.days > 31:
        i = start_date
        while i != end_date:
            i += timedelta(days=1)
            if i.day == 1:
                labels.append(i.strftime('%m.%y'))
    else:
        labels = [(start_date + timedelta(days=i)).strftime('%d.%m') for i in range(dt.days)]

    chartUnit = TruncDay('created_at') if dt.days <= 31 else TruncMonth('created_at')

    income_qs = (Operation.objects
                .filter(
                    created_at__gte = start_date,
                    created_at__lte = end_date,
                    sum__gte = 0,
                    isDebt = False)
                .annotate(period=chartUnit) 
                .values('period')           
                .annotate(total=Sum('sum')) 
                .order_by('period'))

    expenses_qs = (Operation.objects
    .filter(
        created_at__gte = start_date,
        created_at__lte = end_date,
        sum__lte = 0,
        isDebt = False,
    )
    .annotate(period=chartUnit) 
    .values('period')           
    .annotate(total=Sum('sum')) 
    .order_by('period'))

    return render(request, 'register/statistics.html', {
        'labels' : labels,
        'values_1' : [float(s['total']) for s in income_qs],
        'values_2' : [float (s['total']) for s  in expenses_qs],
        'income' : round(float(income_qs.aggregate(Sum("sum", default=0.0))['sum__sum']), 2),
        'expenses' : round(float(expenses_qs.aggregate(Sum("sum",default=0.0))['sum__sum']),2),
        'balance' : round(float(Operation.objects.filter(isDebt=False).aggregate(Sum("sum", default=0.0))['sum__sum']),2),
        'debt' : round(float(Operation.objects.filter(isDebt=True).aggregate(Sum("sum", default=0.0))['sum__sum']), 2)
    })


@login_required
def debts(request):
    # Pass clients and products for edit forms
    clients = Client.objects.all().order_by('lastname', 'firstname')
    products = Product.objects.all().order_by('name')
    types = OperationType.objects.all().order_by('id')

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "edit_operation":
            operation_id = request.POST.get("operation_id")
            operation = Operation.objects.filter(id=operation_id).first()
            if operation:
                # Build changes string
                changes_list = []
                original_author = operation.author
                initially_created = operation.created_at

                # Get new values
                new_type = request.POST.get("type", "").strip()
                new_sum_raw = request.POST.get("sum", "").strip()
                new_client_id = request.POST.get("client") or None
                new_product_id = request.POST.get("product") or None
                new_comments = request.POST.get("comments", "").strip()
                new_date_raw = request.POST.get("date", "").strip()

                # Parse new values
                try:
                    new_sum = Decimal(new_sum_raw) if new_sum_raw else operation.sum
                except (InvalidOperation, TypeError):
                    new_sum = operation.sum

                new_client = Client.objects.filter(id=new_client_id).first() if new_client_id else None
                new_product = Product.objects.filter(id=new_product_id).first() if new_product_id else None

                try:
                    new_date = datetime.strptime(new_date_raw, "%Y-%m-%d") if new_date_raw else operation.created_at
                except ValueError:
                    new_date = operation.created_at

                # Track changes
                if new_type and new_type != operation.type:
                    changes_list.append(f"type:'{operation.type}'->'{new_type}'")
                    operation.type = new_type

                if new_sum != operation.sum:
                    changes_list.append(f"sum:'{operation.sum}'->'{new_sum}'")
                    operation.sum = new_sum

                old_client_name = f"{operation.client.status} {operation.client.firstname} {operation.client.lastname}" if operation.client else "None"
                new_client_name = f"{new_client.status} {new_client.firstname} {new_client.lastname}" if new_client else "None"
                if new_client != operation.client:
                    changes_list.append(f"client:'{old_client_name}'->'{new_client_name}'")
                    operation.client = new_client

                old_product_name = operation.product.name if operation.product else "None"
                new_product_name = new_product.name if new_product else "None"
                if new_product != operation.product:
                    changes_list.append(f"product:'{old_product_name}'->'{new_product_name}'")
                    operation.product = new_product

                if new_comments != (operation.comments or ""):
                    changes_list.append(f"comments:'{operation.comments or ''}'->'{new_comments}'")
                    operation.comments = new_comments if new_comments else None

                if new_date.date() != operation.created_at.date():
                    changes_list.append(f"date:'{operation.created_at.strftime('%Y-%m-%d')}'->'{new_date.strftime('%Y-%m-%d')}'")
                    operation.created_at = new_date

                # Save operation and create change record if there were changes
                if changes_list:
                    operation.save()
                    OperationChange.objects.create(
                        operation=operation,
                        initially_created=initially_created,
                        original_author=original_author,
                        edited_by=request.user,
                        changes=";".join(changes_list)
                    )

            return redirect('debts')

        elif action == "pay_single":
            operation_id = request.POST.get("operation_id")
            operation = Operation.objects.filter(id=operation_id, isDebt=True).first()
            if operation:
                # Mark as paid
                operation.isDebt = False
                operation.save()

                # Update balance
                balance = CurrentBalance.objects.first()
                balance.debt -= operation.sum
                balance.amount += operation.sum
                balance.save()

                # Create debt return operation
                client_name = ""
                if operation.client:
                    client_name = f"{operation.client.status} {operation.client.firstname} {operation.client.lastname}"

                Operation.objects.create(
                    type="DEBT return",
                    sum=operation.sum,
                    client=operation.client,
                    product=None,
                    quantity=None,
                    comments=f"Debt payment for operation #{operation.id}" + (f" - {client_name}" if client_name else ""),
                    isDebt=False,
                    created_at=datetime.now(),
                    author=request.user
                )

        elif action == "pay_all":
            client_id = request.POST.get("client_id")
            client = Client.objects.filter(id=client_id).first()
            if client:
                debt_operations = Operation.objects.filter(client=client, isDebt=True)
                total_sum = debt_operations.aggregate(Sum("sum"))['sum__sum'] or Decimal("0.00")

                # Mark all as paid
                debt_operations.update(isDebt=False)

                # Update balance
                balance = CurrentBalance.objects.first()
                balance.debt -= total_sum
                balance.amount += total_sum
                balance.save()

                # Create debt return operation
                client_name = f"{client.status} {client.firstname} {client.lastname}"

                Operation.objects.create(
                    type="DEBT return",
                    sum=total_sum,
                    client=client,
                    product=None,
                    quantity=None,
                    comments=f"Full debt payment - {client_name}",
                    isDebt=False,
                    created_at=datetime.now(),
                    author=request.user
                )

        return redirect('debts')

    # GET: Group debts by client
    clients_with_debts = []
    clients = Client.objects.filter(operation__isDebt=True).distinct()

    for client in clients:
        debt_operations = Operation.objects.filter(client=client, isDebt=True).order_by('-created_at')
        total_debt = debt_operations.aggregate(Sum("sum"))['sum__sum'] or Decimal("0.00")
        clients_with_debts.append({
            'client': client,
            'operations': debt_operations,
            'total_debt': total_debt
        })

    # Also get debts without client
    no_client_debts = Operation.objects.filter(client__isnull=True, isDebt=True).order_by('-created_at')
    no_client_total = no_client_debts.aggregate(Sum("sum"))['sum__sum'] or Decimal("0.00")

    if no_client_debts.exists():
        clients_with_debts.append({
            'client': None,
            'operations': no_client_debts,
            'total_debt': no_client_total
        })

    return render(request, 'register/debts.html', {
        'clients_with_debts': clients_with_debts,
        'total_debt': sum(c['total_debt'] for c in clients_with_debts),
        'clients': clients,
        'products': products,
        'types': types
    })


@login_required
def sales(request):
    if request.method == "POST":
        # read form data
        sum_raw = request.POST.get("total").strip()
        client_id = request.POST.get("client")
        client_new = request.POST.get("client_new", "").strip()
        product_id = int(request.POST.get("product").split('-')[0])
        quantity_raw = request.POST.get("quantity", "").strip()
        comments = request.POST.get("comments", "").strip() or None
       
        # parse numeric fields
        try:
            sum_val = Decimal(sum_raw) if sum_raw != "" else Decimal("0.00")
        except (InvalidOperation, TypeError):
            sum_val = Decimal("0.00")

        try:
            quantity = int(quantity_raw) if quantity_raw != "" else None
        except (ValueError, TypeError):
            quantity = None

        # resolve/create client: client_new preferred
        client = None
      
        if client_new:
  
            parts = client_new.split(' ')
            status = parts[0] if len(parts) >= 1 else ""
            firstname = parts[1] if len(parts) >= 2 else ""
            lastname = " ".join(parts[2:]) if len(parts) >= 3 else ""
            client = Client.objects.create(status=status, firstname=firstname, lastname=lastname)
            client.save()

        else:
            client = Client.objects.filter(id=client_id).first() if client_id else None
        

        
        # resolve product if provided
        product = Product.objects.filter(id=product_id).first() if product_id else None

        # create operation
        Operation.objects.create(
            type="PURCHASE",
            sum=sum_val,
            client=client,
            product=product,
            quantity=quantity,
            comments=comments,
            isDebt=request.POST.get('isDebt') == 'on',
            created_at=datetime.now(),
            author=request.user
        )
   
        balance = CurrentBalance.objects.first()

        if(request.POST.get('isDebt') != 'on'):
            balance.amount += sum_val
        else:
            balance.debt += sum_val
  
        balance.save()
        
        return redirect(request.path)

	
    operations = Operation.objects.all().order_by('id')
    clients = Client.objects.all().order_by('lastname', 'firstname')
    products = Product.objects.all().order_by('name')
    return render(request, 'register/sales.html', {
		'operations': operations,
		'clients': clients,
		'products': products,
        'types': OperationType.objects.all().order_by('id')
})