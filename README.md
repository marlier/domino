Domino is an open source alerting fronted for any monitoring system. It is backend agnostic, and can receive alerts from ANY source via http calls. It has built in SMS and phone call capabilities using Twilio's API.

Key features
 * alerting via SMS, telephone, and email. (with usage of the API, you can create your own means of alerting)
 * can be used with any existing monitoring solution. Domino does not know or care where the alerts are coming from.
 * automatic escalation of alerts.
 * create teams to direct alert traffic to the right people
 * Ack alerts, get a list of unacked alerts by sending a text message or calling your team's phone number.
 * highly customizable to fit your alerting and escalation procedures
 * Full accessability through the API
 * Get basic stats on your alerts (most frequest, newest, oldest, graphing datapoints, or build your own stats using the API)
 
Documentation
documentation is available on the github wiki.

Denpencies
 * Flask (http://http://flask.pocoo.org/)
 * twilio-python (https://github.com/twilio/twilio-python)
 * MySQLdb (http://sourceforge.net/projects/mysql-python/)
 * Simplejson (http://pypi.python.org/pypi/simplejson/)

Important Notes
 * The server you run Domino on and the mysql server must be in the same timezone (for now)
 * This software does use Twilio (www.twilio.com) to handle SMS and phone calls. If you want to use this, you must setup your own Twilio account.
 * Your Domino-comm.py service must be accessable by twilio's servers can make http calls to it

 
DISCLAIMER
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.