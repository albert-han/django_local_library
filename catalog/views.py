from django.shortcuts import render


# Create your views here.
from .models import Book, Author, BookInstance, Genre

def index(request):
	"""
	View function for home page of site.
	"""
	# Generate counts of some of the main objects
	num_books = Book.objects.all().count()
	num_instances = BookInstance.objects.all().count()
	# Available books (status = 'a')
	num_instances_available = BookInstance.objects.filter(status__exact='a').count()
	num_authors = Author.objects.count() # The 'all()' is implied by default
	num_genres = Genre.objects.all().count()
	num_the = Book.objects.filter(summary__icontains='the').count()

	# Number of visits to this view, as counted in the session variable.
	num_visits=request.session.get('num_visits', 0)
	request.session['num_visits'] = num_visits+1

	# Render the HTML template index.html with the data in the context variable
	return render(
		request,
		'index.html',
		context={'num_books':num_books, 'num_instances':num_instances, 
				 'num_instances_available':num_instances_available,
				 'num_authors':num_authors, 'num_genres':num_genres,
				 'num_the':num_the, 'num_visits':num_visits},
	)

from django.views import generic

class BookListView(generic.ListView):
	model = Book
	paginate_by = 2

#	def get_queryset(self):
#		return Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super(BookListView, self).get_context_data(**kwargs)
		# Get the blog from id and add it to the context
		context['some_data'] = 'This is just some data'
		return context

class BookDetailView(generic.DetailView):
	model = Book


class AuthorListView(generic.ListView):
	model = Author
	paginate_by = 10

	def get_context_data(self, **kwargs):
		context = super(AuthorListView, self).get_context_data(**kwargs)
		context['some_data'] = 'This is just some data'
		return context

class AuthorDetailView(generic.DetailView):
	model = Author

from django.contrib.auth.mixins import LoginRequiredMixin

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
	"""
	Generic class-based view listing books on loan to current user.
	"""
	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 10

	def get_queryset(self):
		return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LoanedBooksForLibrariansListView(LoginRequiredMixin, generic.ListView):
	model = BookInstance
	permission_required = 'catalog.can_mark_returned'
	template_name = 'catalog/bookinstance_list_borrowed_librarian.html'
	paginate_by = 10

	def get_queryset(self):
		return BookInstance.objects.filter(status__exact='o').order_by('due_back')


from django.contrib.auth.decorators import permission_required

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import datetime

from .forms import RenewBookForm

@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
	"""
	View function for renewing a specific BookInstance by librarian
	"""
	book_inst=get_object_or_404(BookInstance, pk=pk)

	# If this is a POST request then process the Form data
	if request.method == 'POST':

		# Create a form instance and populate it with data from the request (binding):
		form = RenewBookForm(request.POST)

		# Check if the form is valid:
		if form.is_valid():
			# process the data in form.cleaned_data as required (here we just write it to the model due_back field)
			book_inst.due_back = form.cleaned_data['renewal_date']
			book_inst.save()

			# redirect to a new URL:
			return HttpResponseRedirect(reverse('librarian-borrowed'))

	# If this is a GET (or any other method) create the default form.
	else:
		proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
		form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

	return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})

from django.forms import ModelForm
from .models import BookInstance
from django.utils.translation import ugettext_lazy as _

class RenewBookModelForm(ModelForm):
	def clean_due_back(self):
		data = self.cleaned_data['due_back']

		#Check date is not in past.
		if data < datetime.date.today():
			raise ValidationError(_('Invalid date - renewal in past'))

		#Check date is in range librarian allowed to change (+4 weeks)
		if data > datetime.date.today() + datetime.timedelta(weeks=4):
			raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

		#Remember to always return the cleaned data
		return data

	class Meta:
		model = BookInstance
		fields = ['due_back',]
		labels = {'due_back': _('Renewal date'),}
		help_texts = {'due_back': _('Enter a date between now and 4 weeks (default 3).'),}

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author

from django.contrib.auth.mixins import PermissionRequiredMixin

class AuthorCreate(PermissionRequiredMixin, CreateView):
	model = Author
	permission_required = 'catalog.can_mark_returned'
	fields = '__all__'
	initial = {'date_of_death':'12/10/2016'}

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
	model = Author
	permission_required = 'catalog.can_mark_returned'
	fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorDelete(PermissionRequiredMixin, DeleteView):
	model = Author
	permission_required = 'catalog.can_mark_returned'
	success_url = reverse_lazy('authors')

class BookCreate(PermissionRequiredMixin, CreateView):
	model = Book
	permission_required = 'catalog.can_mark_returned'
	fields = '__all__'

class BookUpdate(PermissionRequiredMixin, UpdateView):
	model = Book
	permission_required = 'catalog.can_mark_returned'
	fields = '__all__'

class BookDelete(PermissionRequiredMixin, DeleteView):
	model = Book
	permission_required = 'catalog.can_mark_returned'
	success_url = reverse_lazy('books')