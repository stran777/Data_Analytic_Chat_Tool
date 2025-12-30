Option Explicit On
Option Strict On
Imports System
Imports System.IO
Imports System.Text
Imports System.Text.RegularExpressions
Imports System.Reflection
Imports System.Configuration
Imports System.Xml
Imports System.Security


Module ParserCD224
    'Module : "C:\JML\VB.NET\RET8278\ParserCD224\ParserCD224\bin\Release\ParserCD224.exe" 
    'Private Const msFileIn As String = "C:\JML\VB.NET\RET8278\ParserCD224\CMDTest\CD224In.txt"
    'Private Const msFileOut As String = "C:\JML\VB.NET\RET8278\ParserCD224\CMDTest\CD224Out.txt"

    '***Private Const msLogOut As String = "C:\JML\VB.NET\RET8278\CD224Log.txt"

    Dim msFileIn As String = ""
    Dim outputFilename As String = ""
    Dim outputInvalid As String = ""
    Dim outputLogFile As String = ""
    Dim pathCard As String = ""
    Dim CountFlush As Integer = 0
    Dim CountFlushConst As Integer = 100

    Dim mdtStartTime As Date
    Dim mdtEndTime As Date

    Dim TEXT_QUALIFIER_OUTPUT_CARD As String = ConfigurationSettings.AppSettings("TEXTQUALIFIER_OUTPUT_CARD").Replace("'", """")

    Dim CLIENT_ID As String = ConfigurationSettings.AppSettings("CLIENT_ID")
    Dim CLIENT_NUMBER As String = ConfigurationSettings.AppSettings("CLIENT_NUMBER")
    Dim FILE_SOURCE As String = ConfigurationSettings.AppSettings("FILE_SOURCE")
    Dim FILE_TYPE As String = ConfigurationSettings.AppSettings("FILE_TYPE")
    Dim DELEMITER_CARD_NAME As String = ConfigurationSettings.AppSettings("DELEMITER_CARD_NAME")
    '43779 - VW - Paysafe - Process all IPMT FD files into Paysafe
    Dim DELEMITER_CARD_NAME_2 As String = ConfigurationSettings.AppSettings("DELEMITER_CARD_NAME_2")
    Dim HEADER_CARD As String = ConfigurationSettings.AppSettings("HEADER_CARD")
    Dim FILE_EXT_CARD As String = ConfigurationSettings.AppSettings("FILE_EXT_CARD")
    Dim WriteCard As StreamWriter
    Dim DLL_ENCRYPT_PATH As String = ConfigurationSettings.AppSettings("DLL_ENCRYPT_PATH")
    Dim DLL_HASH_PATH As String = ConfigurationSettings.AppSettings("DLL_HASH_PATH")
    Dim HASH_SALT_PATH As String = ConfigurationSettings.AppSettings("HASH_SALT_PATH")
    Dim KEY_ENCRYPT_FILE As String = ""
    Dim SWITCH_ENCRYPT_DATA_CH As String = ConfigurationSettings.AppSettings("SWITCH_ENCRYPT_DATA_CH")
    Dim PATH_XML As String = ConfigurationSettings.AppSettings("PATH_XML")
    Dim PATH_XML_KEYS As String = ConfigurationSettings.AppSettings("PATH_XML_KEYS")
    Dim ATTRIBUTE_CLIENT_ID As String = ConfigurationSettings.AppSettings("ATTRIBUTE_CLIENT_ID")
    Dim ATTRIBUTE_PATH As String = ConfigurationSettings.AppSettings("ATTRIBUTE_PATH")
    Dim SaltString As String = ""

    Dim Cryptor As ParserCryptorInterface.ICryptor
    Function GetCryptor() As ParserCryptorInterface.ICryptor
        Dim ass As Assembly = Assembly.LoadFrom(DLL_ENCRYPT_PATH)
        Dim instance As Object = ass.CreateInstance("ParserEncryptor.Cryptor")
        Dim re As ParserCryptorInterface.ICryptor
        re = CType(instance, ParserCryptorInterface.ICryptor)
        Return re
    End Function

    Dim Hasher As ParserHashInterface.IHash
    Function GetHasher() As ParserHashInterface.IHash
        Dim ass As Assembly = Assembly.LoadFrom(DLL_HASH_PATH)
        Dim instance As Object = ass.CreateInstance("ParserHashData.HashData")
        Dim re As ParserHashInterface.IHash
        re = CType(instance, ParserHashInterface.IHash)
        Return re
    End Function

    Function HashData(ByVal data As String) As String
        Dim re As String = Hasher.HashCardNumber(data + SaltString)
        Return re
    End Function



    Sub GetXMLPathFollowClient()
        If (CLIENT_ID = "") Then
            Return
        End If
        Dim doc As XmlDocument = New XmlDocument()
        doc.Load(PATH_XML)
        Dim nodes As XmlNodeList = doc.SelectNodes(PATH_XML_KEYS)
        If (nodes.Count = 0) Then
            Return
        End If
        For index As Integer = 0 To (nodes.Count - 1)
            Dim clientName As String = nodes(index).Attributes(ATTRIBUTE_CLIENT_ID).Value
            Dim pathXML As String = nodes(index).Attributes(ATTRIBUTE_PATH).Value
            If (clientName = CLIENT_ID) Then
                KEY_ENCRYPT_FILE = pathXML
                Return
            End If
        Next
    End Sub

    Function AddTextQualifierCard(ByVal text As String) As String
        Dim re As StringBuilder = New StringBuilder()
        re.Append(TEXT_QUALIFIER_OUTPUT_CARD)
        re.Append(text)
        re.Append(TEXT_QUALIFIER_OUTPUT_CARD)
        Return re.ToString()
    End Function

    Function AddTextQualifierDelimiterCard(ByVal text As String) As String
        Dim re As StringBuilder = New StringBuilder()
        re.Append("|")
        re.Append(TEXT_QUALIFIER_OUTPUT_CARD)
        re.Append(text)
        re.Append(TEXT_QUALIFIER_OUTPUT_CARD)
        Return re.ToString()
    End Function


    Sub Main(ByVal args() As String)
        'Sub Main()

        Dim iLastIndex As Integer = 0
        Dim inputFilename As String
        Dim Filename As String

        msFileIn = args(0)
        FILE_SOURCE = args(1)
        CLIENT_ID = args(2)
        CLIENT_NUMBER = args(3)

        'msFileIn = "D:\Project US\Parsers\PIVOT\PIVOT_CD224_PARSER\ParserCD224\PIVOT_CRMD7362_CD224_1402181515.txt"

        'inputFilename = msFileIn.Substring(msFileIn.LastIndexOf("\") + 1)

        ''inputFilename = msFileIn

        'If (inputFilename.Contains("\")) Then
        '    Filename = inputFilename.Substring(0, inputFilename.LastIndexOf("\"))
        'Else
        '    Filename = inputFilename
        'End If

        Filename = msFileIn
        Console.WriteLine(Filename)
        Console.WriteLine(inputFilename)

        outputFilename = Filename + "_valid"
        outputInvalid = Filename + "_invalid"
        outputLogFile = Filename + "_log"

        Dim fi As FileInfo = New FileInfo(Filename)
        Dim DATA_FOLDER_NAME As String = fi.DirectoryName + "\"
        '43779 - VW - Paysafe - Process all IPMT FD files into Paysafe
        If (args.Length < 6) Then
            pathCard = DATA_FOLDER_NAME & CLIENT_ID &
                        DELEMITER_CARD_NAME & CLIENT_NUMBER &
                        DELEMITER_CARD_NAME & FILE_TYPE &
                        DELEMITER_CARD_NAME & FILE_SOURCE &
                        DELEMITER_CARD_NAME & "20" & Right(Filename.Trim(), 10) + "00" &
                        DELEMITER_CARD_NAME & FILE_EXT_CARD
        Else
            pathCard = DATA_FOLDER_NAME & CLIENT_ID &
                        DELEMITER_CARD_NAME & CLIENT_NUMBER &
                        DELEMITER_CARD_NAME & FILE_TYPE

            If (args(4).ToUpper() <> "NULL") Then
                pathCard = pathCard &
                            DELEMITER_CARD_NAME_2 & args(4)
            End If

            pathCard = pathCard &
                        DELEMITER_CARD_NAME & FILE_SOURCE

            If (args(5).ToUpper() <> "NULL") Then
                pathCard = pathCard &
                            DELEMITER_CARD_NAME_2 & args(5)
            End If

            pathCard = pathCard &
                        DELEMITER_CARD_NAME & "20" & Right(Filename.Trim(), 10) + "00" &
                        DELEMITER_CARD_NAME & FILE_EXT_CARD
        End If

        If (File.Exists(PATH_XML)) Then
            GetXMLPathFollowClient()
        End If

        If (KEY_ENCRYPT_FILE = "") Then
            Console.WriteLine("- Can not find encrypt key. Maybe Client ID is invalid.")
            Return
        End If

        Cryptor = GetCryptor()
        Cryptor.SetKeyFile(KEY_ENCRYPT_FILE)

        Hasher = GetHasher()
        SaltString = Hasher.GetSaltString(HASH_SALT_PATH)

        mdtStartTime = DateTime.Now
        Call ParseText()
    End Sub



    Sub ParseText()
        Try

            Dim sr1 As StreamReader = New StreamReader(msFileIn)
            Dim sw1 As StreamWriter = New StreamWriter(outputFilename)
            Dim sw2 As StreamWriter = New StreamWriter(outputLogFile)
            Dim swI As StreamWriter = New StreamWriter(outputInvalid)
            WriteCard = New StreamWriter(pathCard)

            Dim sBinNo_1 As String = ""
            Dim sFCDate_2 As String = ""
            Dim sReportDate As String = ""

            Dim sTLOC_3 As String = ""
            Dim sPostStmtDate_4 As String = ""
            Dim sAcqMemb_5 As String = ""
            Dim sBatch_6 As String = ""
            Dim sPRCD_7 As String = ""
            Dim sIssuerAmount_8 As String = ""
            Dim sSPCB_9 As String = ""
            Dim sCurCde_10 As String = ""
            Dim sCardholderAccountNo_11 As String = ""
            Dim sCardholderAccountNoEncrypt As String = ""
            Dim sCardholderAccountNoHash As String = ""
            Dim sFirst6AccountNumber As String = ""
            'Dim sHashedFirst8AccountNumber As String = ""
            Dim sMSAccountNumber As String = ""

            Dim sTranDate_12 As String = ""
            Dim sIssMemb_13 As String = ""
            Dim sTypeRQ_14 As String = ""
            Dim sFileSeqNumber_15 As String = ""
            Dim sCBCode_16 As String = ""

            Dim sMerchantNumber_17 As String = ""
            Dim sBusinessID_18 As String = ""
            Dim sDBPC_19 As String = ""
            Dim sConfRtrvlSupp_20 As String = ""
            Dim s12BLetter_21 As String = ""
            Dim s12BMailFlag_22 As String = ""

            Dim sVisaRequestID_23 As String = ""
            Dim sAcqRfcBin_24 As String = ""
            Dim sAcqPCEndPoint_25 As String = ""
            Dim sPosData_26 As String = ""
            Dim sRA_27 As String = ""

            Dim sRetrieval_28 As String = ""
            Dim sOriginal_29 As String = ""
            Dim sMCImage_30 As String = ""
            Dim sVisaImage_31 As String = ""
            Dim sChargeBack_32 As String = ""

            Dim sMerchantDBAName As String = ""
            Dim sMerchantAddress As String = ""
            Dim sMerchantCity As String = ""
            Dim sMerchantStateOrProvinceCode As String = ""
            Dim sMerchantZipCode As String = ""
            Dim sMerchantTelephoneNum As String = ""

            Dim sHeader As String = ""
            Dim sLineIn As String = ""
            Dim sLineOut As String = ""

            Dim iPos As Integer = 0
            Dim iCount As Integer = 0
            Dim iRequestCount As Integer = 0
            Dim gCount As Integer = 0
            Dim bCount As Integer = 0
            Dim bLineAfterMerchantNumber As Boolean = False

            Dim sSys As String = ""
            Dim sPrin As String = ""

            sHeader = "FCDate" & "|" & "TLOC" & "|" & "PostStmtDate" & "|" &
                      "ACQMemb" & "|" & "Batch" & "|" & "PRCD" & "|" & "IssuerAmount" & "|" & "SPCB" & "|" & "CurCde" &
                      "|CardholderAccountNo|HashedAccountNumber|BinNumber|MSAccountNumber" &
                       "|" & "TranDate" & "|" & "IssMemb" & "|" & "TypeRQ" & "|" &
                      "FileSeqNumber" & "|" & "CBCode" & "|" & "MerchantNumber" & "|" & "BusinessID" & "|" & "DBPC" & "|" &
                      "ConfRtrvlSupp" & "|" & "12BLetter" & "|" & "12BMailFlag" & "|" & "VisaRequestID" & "|" &
                      "AcqRfcBin" & "|" & "AcqPCEndpoint" & "|" & "PosData" & "|" & "RA" & "|" & "SystemNumber" & "|" & "PrinNumber" & "|" &
                      "MerchantDBAName" & "|" & "MerchantAddress" & "|" & "MerchantCity" & "|" & "MerchantStateOrProvinceCode" & "|" & "MerchantZipCode" & "|" & "MerchantTelephoneNum"

            sw1.WriteLine(sHeader)
            WriteCard.WriteLine(HEADER_CARD)

            Dim evaluator As MatchEvaluator = New MatchEvaluator(AddressOf Util.EvaluateMatch)
            Dim regex As Regex = New Regex(Util.REPLACEMENT_REGEX)

            Do

                sLineIn = sr1.ReadLine()
                sLineIn = Util.RemoveDelimiterAndSpecialChars(sLineIn, evaluator, regex)




                '39992
                If bLineAfterMerchantNumber = True Then
                    bLineAfterMerchantNumber = False
                    sMerchantDBAName = Util.RemoveAllUnPrintChar(Trim(Mid(sLineIn, 1, 26)))

                    sMerchantAddress = Trim(Mid(sLineIn, 29, 31))
                    Dim tempsMerchantCity As String = Trim(Mid(sLineIn, 61, 19))
                    Dim outDecimal As Decimal = 0
                    If Decimal.TryParse(tempsMerchantCity.Replace("-", "").Trim(), outDecimal) Then
                        sMerchantTelephoneNum = tempsMerchantCity
                    Else
                        sMerchantCity = tempsMerchantCity
                    End If

                    sMerchantStateOrProvinceCode = Trim(Mid(sLineIn, 80, 2))
                    sMerchantZipCode = Trim(Mid(sLineIn, 83, 26))


                End If

                '' SonT - 07/19/2007
                '' removed IsNumeric(Trim(Mid(sLineIn, 37, 18))) And IsDate(Trim(Mid(sLineIn, 82, 8)))) Or _
                '' at the line after this check <<IsDate(Trim(Mid(sLineIn, 7, 8))>>
                If ((InStr(sLineIn, "CD-224") <> 0 And (InStr(sLineIn, "-FC-") <> 0 Or InStr(sLineIn, "-FN-") <> 0) And InStr(sLineIn, "PAGE") <> 0) Or
                    (InStr(sLineIn, "MERCHANT NUMBER -") <> 0 And InStr(sLineIn, "BUSINESS ID") <> 0 And InStr(sLineIn, "DBPC") <> 0 And
                        InStr(sLineIn, "CONF RTRVL SUPP") <> 0 And InStr(sLineIn, "LETTER") <> 0 And InStr(sLineIn, "MAIL FLAG") <> 0) Or
                    (IsDate(Trim(Mid(sLineIn, 7, 8))) And IsNumeric(Trim(Mid(sLineIn, 25, 8)))) Or
                    (InStr(sLineIn, "VISA REQUEST ID") <> 0 And InStr(sLineIn, "ACQ PC ENDPOINT") <> 0 And
                        InStr(sLineIn, "POS DATA") <> 0 And InStr(sLineIn, "RA") <> 0) Or
                    (InStr(sLineIn, "RETRIEVAL REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Or
                    (InStr(sLineIn, "ORIGINAL REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Or
                    (InStr(sLineIn, "MC IMAGE REQUEST") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Or
                    (InStr(sLineIn, "VISA IMAGE REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Or
                    (InStr(sLineIn, "CHARGEBACK REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10))))) Then

                    If (InStr(sLineIn, "CD-224") <> 0 And (InStr(sLineIn, "-FC-") <> 0 Or InStr(sLineIn, "-FN-") <> 0) And InStr(sLineIn, "PAGE") <> 0) Then

                        sBinNo_1 = ""
                        sFCDate_2 = ""

                        sTLOC_3 = ""
                        sPostStmtDate_4 = ""
                        sAcqMemb_5 = ""
                        sBatch_6 = ""
                        sPRCD_7 = ""
                        sIssuerAmount_8 = ""
                        sSPCB_9 = ""
                        sCurCde_10 = ""
                        sCardholderAccountNo_11 = ""
                        sTranDate_12 = ""
                        sIssMemb_13 = ""
                        sTypeRQ_14 = ""
                        sFileSeqNumber_15 = ""
                        sCBCode_16 = ""

                        sMerchantNumber_17 = ""
                        sBusinessID_18 = ""
                        sDBPC_19 = ""
                        sConfRtrvlSupp_20 = ""
                        s12BLetter_21 = ""
                        s12BMailFlag_22 = ""

                        sVisaRequestID_23 = ""
                        sAcqRfcBin_24 = ""
                        sAcqPCEndPoint_25 = ""
                        sPosData_26 = ""
                        sRA_27 = ""

                        iPos = InStr(sLineIn, "CD-224")
                        sBinNo_1 = Trim(Mid(sLineIn, iPos + 9, 9))

                        If (sLineIn.Contains("-FC-")) Then
                            iPos = InStr(sLineIn, "-FC-")
                        ElseIf (sLineIn.Contains("-FN-")) Then
                            iPos = InStr(sLineIn, "-FN-")
                        End If
                        sFCDate_2 = Trim(Mid(sLineIn, iPos + 5, 8))

                        sSys = Trim(Mid(sLineIn, 11, 4))
                        sPrin = Trim(Mid(sLineIn, 16, 4))

                    End If


                    If (InStr(sLineIn, "MERCHANT NUMBER -") <> 0 And InStr(sLineIn, "BUSINESS ID") <> 0 And
                        InStr(sLineIn, "DBPC") <> 0 And InStr(sLineIn, "CONF RTRVL SUPP") <> 0 And
                        InStr(sLineIn, "LETTER") <> 0 And InStr(sLineIn, "MAIL FLAG") <> 0) Then

                        'sMerchantNumber_17 = ""
                        'sBusinessID_18 = ""
                        'sDBPC_19 = ""
                        'sConfRtrvlSupp_20 = ""
                        's12BLetter_21 = ""
                        's12BMailFlag_22 = ""

                        iPos = InStr(sLineIn, "MERCHANT NUMBER -")
                        sMerchantNumber_17 = Trim(Mid(sLineIn, iPos + 18, 16))
                        bLineAfterMerchantNumber = True

                        iPos = InStr(sLineIn, "BUSINESS ID")
                        sBusinessID_18 = Trim(Mid(sLineIn, iPos + 12, 10))

                        iPos = InStr(sLineIn, "DBPC")
                        sDBPC_19 = Trim(Mid(sLineIn, iPos + 5, 2))

                        iPos = InStr(sLineIn, "CONF RTRVL SUPP")
                        sConfRtrvlSupp_20 = Trim(Mid(sLineIn, iPos + 17, 1))

                        iPos = InStr(sLineIn, "LETTER")
                        s12BLetter_21 = Trim(Mid(sLineIn, iPos + 8, 1))

                        iPos = InStr(sLineIn, "MAIL FLAG")
                        s12BMailFlag_22 = Trim(Mid(sLineIn, iPos + 10, 5))

                    End If

                    'jml 04/18/2007  took out IsNumeric(Trim(Mid(sLineIn, 18, 6)))
                    'If (IsDate(Trim(Mid(sLineIn, 7, 8))) And IsNumeric(Trim(Mid(sLineIn, 18, 6))) And _
                    '    IsNumeric(Trim(Mid(sLineIn, 25, 8))) And IsNumeric(Trim(Mid(sLineIn, 37, 18))) And _
                    '    IsNumeric(Trim(Mid(sLineIn, 65, 16))) And IsDate(Trim(Mid(sLineIn, 82, 8))) And _
                    '    IsNumeric(Trim(Mid(sLineIn, 93, 6))) And IsNumeric(Trim(Mid(sLineIn, 115, 11)))) Then

                    '' SonT - 07/19/2007 - removed some constraints from here
                    If (IsDate(Trim(Mid(sLineIn, 7, 8))) And IsNumeric(Trim(Mid(sLineIn, 25, 8))) And IsNumeric(Trim(Mid(sLineIn, 65, 16))) And
                        IsNumeric(Trim(Mid(sLineIn, 93, 6))) And IsNumeric(Trim(Mid(sLineIn, 115, 11)))) Then

                        sTLOC_3 = Trim(Mid(sLineIn, 3, 3))

                        sPostStmtDate_4 = Trim(Mid(sLineIn, 7, 8))

                        sAcqMemb_5 = Trim(Mid(sLineIn, 18, 6))

                        sBatch_6 = Trim(Mid(sLineIn, 25, 8))

                        sPRCD_7 = Trim(Mid(sLineIn, 34, 2))

                        sIssuerAmount_8 = Trim(Mid(sLineIn, 37, 18))

                        sSPCB_9 = Trim(Mid(sLineIn, 56, 3))

                        sCurCde_10 = Trim(Mid(sLineIn, 59, 3))

                        sCardholderAccountNo_11 = Trim(Mid(sLineIn, 65, 16))
                        sCardholderAccountNoEncrypt = Cryptor.EncryptData(sCardholderAccountNo_11)
                        sCardholderAccountNoHash = HashData(sCardholderAccountNo_11)
                        Dim sCardholderAccountNoFirst12 As String = Left(sCardholderAccountNo_11, 12)
                        sFirst6AccountNumber = Left(sCardholderAccountNo_11, 6)
                        'sHashedFirst8AccountNumber = HashData(Left(sCardholderAccountNo_11, 8))
                        sMSAccountNumber = Right(sCardholderAccountNo_11, 4)
                        'sCardholderAccountNoFirst12Encrypt = Cryptor.EncryptData(sCardholderAccountNoFirst12)
                        'sCardholderAccountNoFirst12Hash = HashData(sCardholderAccountNoFirst12)

                        sTranDate_12 = Trim(Mid(sLineIn, 82, 8))

                        sIssMemb_13 = Trim(Mid(sLineIn, 93, 6))

                        sTypeRQ_14 = Trim(Mid(sLineIn, 101, 11))

                        sFileSeqNumber_15 = Trim(Mid(sLineIn, 113, 13))

                        sCBCode_16 = Trim(Mid(sLineIn, 128, 5))

                    End If

                    'jml 04/18/2007  took out InStr(sLineIn, "ACQ RFC BIN") <> 0
                    'If (InStr(sLineIn, "VISA REQUEST ID") <> 0 And InStr(sLineIn, "ACQ RFC BIN") <> 0 And _
                    '    InStr(sLineIn, "ACQ PC ENDPOINT") <> 0 And InStr(sLineIn, "POS DATA") <> 0 And InStr(sLineIn, "RA") <> 0) Then

                    If (InStr(sLineIn, "VISA REQUEST ID") <> 0 And
                        InStr(sLineIn, "ACQ PC ENDPOINT") <> 0 And InStr(sLineIn, "POS DATA") <> 0 And InStr(sLineIn, "RA") <> 0) Then

                        'sVisaRequestID_23 = ""
                        'sAcqRfcBin_24 = ""
                        'sAcqPCEndPoint_25 = ""
                        'sPosData_26 = ""
                        'sRA_27 = ""

                        iPos = InStr(sLineIn, "VISA REQUEST ID")
                        sVisaRequestID_23 = Trim(Mid(sLineIn, iPos + 16, 12))

                        '04/17/2007 "ACQ RFC BIN" Missing 
                        'iPos = InStr(sLineIn, "ACQ RFC BIN")
                        'sAcqRfcBin_24 = Trim(Mid(sLineIn, iPos + 12, 7))

                        iPos = InStr(sLineIn, "ACQ PC ENDPOINT")
                        sAcqPCEndPoint_25 = Trim(Mid(sLineIn, iPos + 16, 9))

                        iPos = InStr(sLineIn, "POS DATA")
                        sPosData_26 = Trim(Mid(sLineIn, iPos + 10, 12))

                        iPos = InStr(sLineIn, "RA")
                        sRA_27 = Trim(Mid(sLineIn, iPos + 3, 5))

                        sLineOut = Trim(sFCDate_2) & "|" & Trim(sTLOC_3) & "|" & Trim(sPostStmtDate_4) & "|" &
                                   Trim(sAcqMemb_5) & "|" & Trim(sBatch_6) & "|" & Trim(sPRCD_7) & "|" & Trim(sIssuerAmount_8) & "|" &
                                   Trim(sSPCB_9) & "|" & Trim(sCurCde_10)


                        If (SWITCH_ENCRYPT_DATA_CH <> "OFF") Then
                            sLineOut = sLineOut & "|" & Trim(sCardholderAccountNoEncrypt)
                        Else
                            sLineOut = sLineOut & "|" & ""
                        End If

                        sLineOut = sLineOut & "|" & Trim(sCardholderAccountNoHash)
                        sLineOut = sLineOut & "|" & Trim(sFirst6AccountNumber)
                        sLineOut = sLineOut & "|" & Trim(sMSAccountNumber)

                        sLineOut = sLineOut & "|" & Trim(sTranDate_12) & "|" &
                                    Trim(sIssMemb_13) & "|" & Trim(sTypeRQ_14) & "|" & Trim(sFileSeqNumber_15) &
                                    "|" & Trim(sCBCode_16) & "|" &
                                   Trim(sMerchantNumber_17) & "|" & Trim(sBusinessID_18) & "|" & Trim(sDBPC_19) & "|" &
                                   Trim(sConfRtrvlSupp_20) & "|" & Trim(s12BLetter_21) & "|" & Trim(s12BMailFlag_22) & "|" &
                                   Trim(sVisaRequestID_23) & "|" & Trim(sAcqRfcBin_24) & "|" & Trim(sAcqPCEndPoint_25) & "|" &
                                   Trim(sPosData_26) & "|" & Trim(sRA_27) & "|" & Trim(sSys) & "|" & Trim(sPrin) & "|" &
                                   Trim(sMerchantDBAName) & "|" & Trim(sMerchantAddress) & "|" & Trim(sMerchantCity) & "|" & Trim(sMerchantStateOrProvinceCode) & "|" &
                                   Trim(sMerchantZipCode) & "|" & Trim(sMerchantTelephoneNum)
                        '& "|" & Trim(sHashedFirst8AccountNumber)

                        'sw1.WriteLine(sLineOut)

                        iCount = iCount + 1

                        If (IsDate(sFCDate_2) And IsDate(sTranDate_12) And IsNumeric(sIssuerAmount_8)) _
                            And Util.CheckValidMerchant(sMerchantNumber_17) Then
                            sw1.WriteLine(sLineOut)
                            Dim cardInfo As StringBuilder = New StringBuilder()
                            cardInfo.Append(AddTextQualifierCard(sCardholderAccountNoHash))
                            cardInfo.Append(AddTextQualifierDelimiterCard(sCardholderAccountNoEncrypt))
                            WriteCard.WriteLine(cardInfo.ToString())
                            gCount = gCount + 1

                            CountFlush = CountFlush + 1
                            If (CountFlush > CountFlushConst) Then
                                sw1.Flush()
                                WriteCard.Flush()
                                CountFlush = 0
                            End If

                            If (sReportDate = "") Then
                                Dim dReportDate As DateTime = DateTime.Now
                                If (DateTime.TryParse(sFCDate_2, dReportDate)) Then
                                    dReportDate = dReportDate.AddDays(1)
                                    sReportDate = dReportDate.ToString("MM/dd/yyyy")
                                End If
                            End If
                        Else
                            swI.WriteLine(sFCDate_2 & ", " & sTranDate_12 & ", " & sIssuerAmount_8 & " ----> " & sLineOut)
                            bCount = bCount + 1
                        End If

                    End If

                    If (InStr(sLineIn, "RETRIEVAL REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Then
                        iPos = InStr(sLineIn, "RETRIEVAL REQUESTS")
                        sRetrieval_28 = Trim(Mid(sLineIn, iPos + 26, 13))
                        iRequestCount = iRequestCount + CInt(sRetrieval_28)
                    End If

                    If (InStr(sLineIn, "ORIGINAL REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Then
                        iPos = InStr(sLineIn, "ORIGINAL REQUESTS")
                        sOriginal_29 = Trim(Mid(sLineIn, iPos + 26, 13))
                        iRequestCount = iRequestCount + CInt(sOriginal_29)
                    End If

                    If (InStr(sLineIn, "MC IMAGE REQUEST") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Then
                        iPos = InStr(sLineIn, "MC IMAGE REQUEST")
                        sMCImage_30 = Trim(Mid(sLineIn, iPos + 26, 13))
                        iRequestCount = iRequestCount + CInt(sMCImage_30)
                    End If

                    If (InStr(sLineIn, "VISA IMAGE REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Then
                        iPos = InStr(sLineIn, "VISA IMAGE REQUESTS")
                        sVisaImage_31 = Trim(Mid(sLineIn, iPos + 26, 13))
                        iRequestCount = iRequestCount + CInt(sVisaImage_31)
                    End If

                    If (InStr(sLineIn, "CHARGEBACK REQUESTS") <> 0 And IsNumeric(Trim(Mid(sLineIn, 31, 10)))) Then
                        iPos = InStr(sLineIn, "CHARGEBACK REQUESTS")
                        sChargeBack_32 = Trim(Mid(sLineIn, iPos + 26, 13))
                        iRequestCount = iRequestCount + CInt(sChargeBack_32)
                    End If

                End If

            Loop Until sLineIn Is Nothing

            mdtEndTime = DateTime.Now

            sw2.WriteLine("FileType:CD224")
            sw2.WriteLine("TotalRecordCount:{0}", iCount.ToString())
            sw2.WriteLine("GoodRecordCount:{0}", gCount.ToString())
            sw2.WriteLine("BadRecordCount:{0}", bCount.ToString())
            sw2.WriteLine("FileTrailer:1")
            sw2.WriteLine("MatchedRecordCounts:1")
            sw2.WriteLine("FileTrailerDataMatched:1")
            sw2.WriteLine("ReportDate:{0}", sReportDate)

            sr1.Close()
            sw1.Close()
            sw2.Close()
            swI.Close()
            WriteCard.Close()

            sr1.Dispose()
            sw1.Dispose()
            sw2.Dispose()
            swI.Dispose()
            WriteCard.Dispose()

        Catch ex As Exception
            Console.WriteLine("The process failed: {0}", ex.ToString)
        End Try

    End Sub

End Module
