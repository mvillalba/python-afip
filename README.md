python-afip
===========

Python package to interact with some of Argentina's AFIP Web services.

*NOTE: UNDER DEVELOPMENT. NOT FULLY IMPLEMENTED*

It implements programmatic interfaces for the following services:
 * WSAA: the token-granting service.
 * WSFE: the invoicing ("factura") service for the local market (type "C" invoices). [PARTIALLY IMPLEMENTED]
 * WSFEX: the invoice service for export operations (type "E" invoices).
 * WS_SR_PADRON_A5: tax payer information service (query to get info for your invoices).
 * WS_SR_PADRON_A13: same as above, but output is different.
 
It's designed to contain anything a _monotributista_ freelancer reasonably needs to issue
and manipulate invoices, presumably to send something that doesn't look completely horrendous and
unprofessional to clients (I'm looking at you, RECE et al.)

This is a Python 3 ONLY library, seeing as Python 2.7 will reach end of life in short order.

This package only contains the base interfaces to interact with AFIP's Web services. It doesn't
implement a DB backend to store things on, an administrative interface of any kind, or an invoice/receipt
template-to-PDF generator. It does, however, include a CLI utility to test things out.

Tested only on Linux as that's what I use, but there is nothing platform-specific about it. If you
use it on Mac/Windows/whatever and it something doesn't work, kindly submit a pull request or at least
file a bug.

Contribution in the form of bug fixes, documentation, code improvements, tests, support for additional
services.

You might notice there is another package available for Python to interact with AFIP's services called
pyafipws and you might be wondering why use this one instead. To that, I can tell you why I'm writing
it:
 * This is a simpler, one-function-one-package sort of deal. Use it to build something else.
 * It runs on Python 3 (and only Python 3) out of the box.
 * The code is simpler/cleaner to understand.
 * This package tries to abstract away (i.e. hide) the inherent ugliness and the sea of inconsistencies
   in the native interfaces and gives you more natural data structures that don't make you feel like you
   are dealing with an ugly pile of XML documents and related SOAP awfulness. Because you are not, I am,
   so you don't have to.

And just to be fair, a few reasons not to use it:
 * You want something established and better tested.
 * You need services not currently supported.
 * You don't care about Python 3 (though you should, really, it's pretty sweet).
 * You aren't looking to integrate this into something else. You want a fully built out solution.
 
 
 TODO
 ----
  * Document how to get valid certificates.
  * Document basic usage of each service.
  * Document API in code for API reference doc gen.
  * Implement WSFE.
  * Test WSFE in production.
  * Test WSFEX in production.
  * Implement output of invoices into whatever storage format AFIP requires as well as something
    nicer to deal with.


Logging
-------
In the event anything goes wrong either in this package or in your own application code, and given the
irrevocable nature of issuing an invoice through AFIP (why?!), good logging is essential. So, all
interfaces run a logging plugin on the underlying SOAP client.

All you need to do is pass the _log_dir_ argument to the constructor of any WS client. You'll get
jsonlines-formatted files with every request and response sent/received along with the raw XML and
timestamps for whatever service you called.

I strongly encourage you to use this. Worst-case scenario, you'll have a small log directory to
clean up every now and then.


Documentation
-------------
For now, this file is all the documentation you get. I'll be adding to it over the coming days/weeks. However,
here are some pointers:
 - AFIP has documentation on how to get working certificates (start with a testing certificate only).
 - Play with the CLI tool. It can call anything that's implemented and lets you interact with the different web
   services. Run "python -m afip --help" to get started.
 - Load your certificate into the CLI tool with the _profile_ sub-command.
 - Get usable tokens (they'll be stored for your convenience) from the WSAA service via the wsaa sub-command.
   Try "python -m afip wsaa authorize wsfex".
 - Interact with services you've requested tokens for (they expire after 12 hours) with the appropriate sub-command.
   Try "python -m afip wsfex country_cuits".
 - To see how to use it in code, import the appropriate client from the appropriately-named module and instantiate it
   with an afip.credentials.AFIPCredentials object, a log dir, and a Zeep cache of some sort. The last 2 are optional,
   but a log directory will give you crucial debugging information and a Zeep cache will speed up your app as Zeep
   (the SOAP client library) will be able to cache WSDL files. See afip.ws.WebServiceTool for a working example;
   specifically, the constructor and the _handle_ method. There is also an example of how to use each individual
   method of a client in the same file the client is defined, in the code for the CLI sub-command for it (look for
   a sub-class of WebServiceTool).
