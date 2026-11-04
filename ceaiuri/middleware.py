from .accesari import Accesare, accesari

class AccesareMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.ip_client = request.META.get("REMOTE_ADDR", "")
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.resolver_match.app_name != "ceaiuri":
            return

        parametri = {}
        for nume, valoare in request.GET.items():
            if valoare == "":
                valoare = None
            parametri[nume] = valoare

        request.accesare = Accesare(
            ip_client=request.ip_client,
            url=request.build_absolute_uri(),
            parametri=parametri,
        )
        accesari.append(request.accesare)
        print(request.accesare, flush=True)
