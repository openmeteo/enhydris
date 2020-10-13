import re


def get_formset_parameters(client, url):
    """Return TOTAL_FORMS and INITIAL_FORMS parameters for all formsets.

    When we POST a form in order to add an object to django admin, we also need to
    specify TOTAL_FORMS and INITIAL_FORMS for each formset. For example, if we want to
    POST a book and it has an "authors" formset, we need to specify authors-TOTAL_FORMS
    and authors-INITIAL_FORMS. If we don't do this will get the error "ManagementForm
    data is missing or has been tampered with".

    This function makes a GET request, automatically finds the formsets in the html
    returned, and returns a dictionary containing all necessary TOTAL_FORMS and
    INITIAL_FORMS parameters set to zero. In the above book/authors example, it would
    return {"authors-TOTAL_FORMS": 0, "authors-INITIAL_FORMS": 0}.

    Arguments:
        - client: The Django test client
        - url: The URL to which we'll later POST, such as /admin/library/books/add/
    """
    response = client.get(url)
    formsets = re.findall(r'id="([^"]*)-group"', response.content.decode())
    result = {}
    for formset in formsets:
        result[f"{formset}-TOTAL_FORMS"] = 0
        result[f"{formset}-INITIAL_FORMS"] = 0
    return result
