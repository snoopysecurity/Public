using System;
using System.Diagnostics;
using System.Xml;
using System.Xml.Serialization;
using System.IO;
using System.Text;

namespace DeserializeConsoleApp
{

    /*

<customRootNode>
<item objectType="DeserializeConsoleApp.ExecCMD, DeserializeConsoleApp, Version=1.0.0.0,
Culture=neutral, PublicKeyToken=null">
<ExecCMD xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<cmd>calc.exe</cmd>
</ExecCMD>
</item>
</customRootNode>
*/

    class Program
    {
        static void Main(string[] args)
        {

            Console.WriteLine("Insert Base64 encoded XML data to Deserialize:");
            var input = Console.ReadLine();
            byte[] db = Convert.FromBase64String(input);
            string decodedData = Encoding.UTF8.GetString(db);
            CustomDeserializer(decodedData);
            Console.WriteLine(decodedData);
        }
        static void CustomDeserializer(String myXMLString)
        {
            XmlDocument xmlDocument = new XmlDocument();
            xmlDocument.LoadXml(myXMLString);
            foreach (XmlElement xmlItem in xmlDocument.SelectNodes("customRootNode/item"))
            {
                string typeName = xmlItem.GetAttribute("objectType");
                var xser = new XmlSerializer(Type.GetType(typeName));
                var reader = new XmlTextReader(new StringReader(xmlItem.InnerXml));
                xser.Deserialize(reader);
            }
        }
    }

    public class ExecCMD
    {
        private String _cmd;
        public String cmd
        {
            get { return _cmd; }
            set
            {
                _cmd = value;
                ExecCommand();
            }
        }

        private void ExecCommand()
        {
            Process myProcess = new Process();
            myProcess.StartInfo.FileName = _cmd;
            myProcess.Start();
            myProcess.Dispose();
        }
    }


}

