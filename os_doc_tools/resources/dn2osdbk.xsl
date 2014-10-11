<?xml version="1.0" encoding="UTF-8" ?>
<!--
#=======
# Dn2dbk
#=======
#
# :author: Eric Bellot
# :email: ebellot@netcourrier.com
# :date: 2003-02-27
# :version: 0.3.1
# :Copyright: Copyright© 2003, Eric Bellot
#
# This script is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

-->
<xsl:stylesheet version="1.1"
                xmlns="http://docbook.org/ns/docbook"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xlink="http://www.w3.org/1999/xlink">

<xsl:output method="xml" indent="yes" omit-xml-declaration="no"/>

<xsl:strip-space elements="*"/>

<xsl:template match="/document/section">
<toplevel xmlns="http://docbook.org/ns/docbook"
  xmlns:xi="http://www.w3.org/2001/XInclude"
  xmlns:xlink="http://www.w3.org/1999/xlink" version="5.0">
    <xsl:attribute name="xml:id">
        <xsl:value-of select="translate(@ids,':','_')"/>
    </xsl:attribute>
    <xsl:apply-templates/>
</toplevel>
</xsl:template>

<!--
ARTICLEINFO
-->

<xsl:template name="articleinfo">
    <articleinfo>
        <xsl:apply-templates select="/document/title" mode="articleinfo"/>
        <xsl:apply-templates select="/document/docinfo" mode="articleinfo"/>
        <xsl:apply-templates select="/document/topic[@class='abstract']"
                             mode="articleinfo"/>
        <xsl:apply-templates select="/document/topic[@class='dedication']"
                             mode="articleinfo"/>
    </articleinfo>
</xsl:template>

<xsl:template match="/document/title"/>

<xsl:template match="title" mode="articleinfo">
    <title>
        <xsl:apply-templates/>
    </title>
</xsl:template>

<xsl:template match="docinfo"/>

<xsl:template match="docinfo" mode="articleinfo">
    <xsl:apply-templates/>
</xsl:template>

<xsl:template match="authors">
    <authorgroup>
        <xsl:apply-templates/>
    </authorgroup>
</xsl:template>

<xsl:template match="author">
    <author>
        <othername>
            <xsl:apply-templates/>
        </othername>
        <xsl:call-template name="affiliation"/>
     </author>
</xsl:template>

<xsl:template match="contact/reference"/>

<xsl:template match="contact">
    <bibliomisc>
        <email>
            <xsl:value-of select="normalize-space(string(reference))"/>
        </email>
    </bibliomisc>
</xsl:template>

<xsl:template match="date">
    <pubdate>
        <xsl:apply-templates/>
    </pubdate>
</xsl:template>

<xsl:template match="/document/topic[@class='abstract']"/>

<xsl:template match="topic" mode="articleinfo">
    <xsl:if test="@class='abstract'">
        <abstract>
            <xsl:apply-templates select="paragraph"/>
        </abstract>
    </xsl:if>
</xsl:template>

<xsl:template name="affiliation">
    <xsl:if test="../organization or normalize-space(
                  string(../field/field_name))='jobtitle'">
        <affiliation>
            <xsl:apply-templates select="../field
            [normalize-space(field_name)='jobtitle']"
            mode="articleinfo"/>
            <xsl:apply-templates select="../organization"
                                 mode="articleinfo"/>
        </affiliation>
    </xsl:if>
</xsl:template>

<xsl:template match="field[normalize-space(field_name)='jobtitle']"/>

<xsl:template match="field[normalize-space(field_name)='jobtitle']"
              mode="articleinfo">
   <jobtitle>
        <xsl:apply-templates select="field_body/paragraph[1]/node()"/>
   </jobtitle>
</xsl:template>

<xsl:template match="organization"/>

<xsl:template match="organization" mode="articleinfo">
    <orgname>
        <xsl:apply-templates/>
    </orgname>
</xsl:template>

<xsl:template match="status"/>

<xsl:template match="version">
    <releaseinfo>
        <xsl:apply-templates/>
    </releaseinfo>
</xsl:template>

<xsl:template match="copyright">
    <xsl:param name="ct" select="normalize-space(string(.))"/>
    <xsl:if test="normalize-space(substring-before($ct,'©'))='Copyright'
                  or normalize-space(substring-before($ct,'©'))='copyright'">
        <copyright>
            <year>
                <xsl:value-of
                select="normalize-space(substring-before(substring-after($ct,'©'),','))"/>
            </year>
            <holder>
                <xsl:value-of
                select="normalize-space(substring-after(substring-after($ct,'©'),','))"/>
            </holder>
        </copyright>
    </xsl:if>
</xsl:template>

<xsl:template match="address">
    <address>
        <xsl:apply-templates/>
    </address>
</xsl:template>

<xsl:template match="docinfo/field">
    <xsl:choose>
        <xsl:when test="normalize-space(field_name)='legalnotice' or
                        normalize-space(field_name)='Legalnotice'">
            <legalnotice>
                <xsl:apply-templates select="field_body"/>
            </legalnotice>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>

<xsl:template match="*" mode="notags">
    <xsl:apply-templates mode="notags"/>
</xsl:template>

<xsl:template match="topic[@class='dedication']"/>

<xsl:template match="topic[@class='dedication']" mode="articleinfo">
    <dedication>
        <xsl:apply-templates/>
    </dedication>
</xsl:template>

<!-- TOC -->
<xsl:template match="topic[@class='contents']">
   <toc>
        <xsl:apply-templates select="title" mode="titletoc"/>
        <tocchap>
        <xsl:apply-templates mode="toc"/>
   </tocchap></toc>
</xsl:template>

<xsl:template match="title" mode="toc"/>

<xsl:template match="title" mode="titletoc">
    <xsl:apply-templates select="."/>
</xsl:template>

<xsl:template match="bullet_list" mode="toc">
    <xsl:param name="level" select="count(ancestor::bullet_list)"/>
    <xsl:choose>
        <xsl:when test="$level=0">
            <xsl:apply-templates mode="toc"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:element name="{concat('toclevel',$level)}">
                <xsl:apply-templates mode="toc"/>
            </xsl:element>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="list_item" mode="toc">
    <tocentry>
        <xsl:attribute name="xml:id">
            <xsl:value-of select="paragraph/reference/@id"/>
        </xsl:attribute>
        <xsl:attribute name="linkend">
            <xsl:value-of select="paragraph/reference/@refid"/>
        </xsl:attribute>
         <xsl:apply-templates select="paragraph/reference/node()" mode="toc"/>
    </tocentry>
        <xsl:apply-templates select="bullet_list" mode="toc"/>
</xsl:template>

<!--
BODY
-->

<xsl:template match="section">
    <section>
        <xsl:attribute name="xml:id">
            <xsl:value-of select="translate(@ids,':','_')"/>
        </xsl:attribute>
        <xsl:if test="count(ancestor::section)=1">
            <xsl:processing-instruction name="dbhtml stop-chunking"/>
        </xsl:if>
        <xsl:apply-templates/>
    </section>
</xsl:template>

<xsl:template match="title">
    <title>
        <xsl:apply-templates/>
    </title>
</xsl:template>

<xsl:template match="paragraph|compact_paragraph|inline|rubric">
    <para>
        <xsl:apply-templates/>
    </para>
</xsl:template>

<xsl:template match="literal_block|doctest_block">
    <programlisting>
    <xsl:if test="@language != ''">
        <xsl:attribute name="language">
            <xsl:value-of select="@language"/>
        </xsl:attribute>
    </xsl:if>
    <xsl:if test="name(current())='doctest_block'">
        <xsl:attribute name="role">
            <xsl:value-of select="'doctest'"/>
        </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates /></programlisting>
</xsl:template>

<xsl:template match="line_block">
    <literallayout>
        <xsl:apply-templates />
    </literallayout>
</xsl:template>

<xsl:template match="block_quote">
    <blockquote>
        <xsl:apply-templates/>
    </blockquote>
</xsl:template>

<xsl:template match="bullet_list">
    <itemizedlist>
        <xsl:if test="@mark">
            <xsl:attribute name="mark">
                <xsl:value-of select="@bullet"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
    </itemizedlist>
</xsl:template>

<xsl:template match="enumerated_list">
    <orderedlist>
        <xsl:attribute name="numeration">
            <xsl:value-of select="@enumtype"/>
        </xsl:attribute>
        <xsl:apply-templates/>
    </orderedlist>
</xsl:template>

<xsl:template match="definition_list|option_list">
    <xsl:param name="role" select="name(current())"/>
    <variablelist>
        <xsl:attribute name="role">
            <xsl:value-of select="$role"/>
        </xsl:attribute>
        <xsl:apply-templates/>
    </variablelist>
</xsl:template>

<xsl:template match="definition_list_item|option_list_item">
    <varlistentry>
        <xsl:apply-templates/>
    </varlistentry>
</xsl:template>

<xsl:template match="term|option_group">
    <term>
        <xsl:if test="following-sibling::classifier">
            <xsl:attribute name="role">
                <xsl:value-of select="following-sibling::classifier"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
    </term>
</xsl:template>

<xsl:template match="classifier"/>

<xsl:template match="option">
    <option>
        <xsl:apply-templates/>
    </option>
    <xsl:if test="following-sibling::option">
        <xsl:value-of select="', '"/>
    </xsl:if>
</xsl:template>

<xsl:template match="option_string">
    <xsl:apply-templates/>

</xsl:template>

<xsl:template match="option_argument">
    <xsl:if test="@delimiter">
        <xsl:value-of select="@delimiter"/>
    </xsl:if>
    <replaceable>
        <xsl:apply-templates/>
    </replaceable>
</xsl:template>

<xsl:template match="list_item|definition|description">
    <xsl:choose>
        <xsl:when test="normalize-space(.)">
            <listitem>
                <xsl:apply-templates/>
            </listitem>
        </xsl:when>
        <xsl:otherwise>
            <listitem><para>???</para></listitem>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="field_name[not(ancestor::docinfo)]">
    <xsl:choose>
        <xsl:when test="normalize-space(string(.))='attribution' or
                        normalize-space(string(.))='Attribution'">
            <attribution>
                <xsl:apply-templates select="../field_body" mode="attribution"/>
            </attribution>
        </xsl:when>
        <xsl:otherwise>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="field_body[not(ancestor::docinfo)]"/>

<xsl:template match="field_body" mode="attribution">
    <xsl:apply-templates select="paragraph[1]/*|paragraph[1]/text()"/>
</xsl:template>

<xsl:template match="paragraph[interpreted/@role='title']">
    <xsl:apply-templates/>
</xsl:template>

<!--
INLINETAGS
-->
<xsl:template match="emphasis">
    <emphasis>
        <xsl:apply-templates/>
    </emphasis>
</xsl:template>

<xsl:template match="strong">
    <xsl:choose>
        <xsl:when test="@classes='command'">
            <command>
                <xsl:apply-templates/>
            </command>
        </xsl:when>
        <xsl:otherwise>
            <emphasis>
                <xsl:attribute name="role">
                    <xsl:apply-templates/>
                </xsl:attribute>
            </emphasis>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="literal">
    <literal>
        <xsl:apply-templates/>
    </literal>
</xsl:template>

<xsl:template match="title_reference">
    <citetitle>
        <xsl:apply-templates/>
    </citetitle>
</xsl:template>

<xsl:template match="raw">
    <xsl:if test="@format='docbook'">
        <xsl:value-of disable-output-escaping="yes" select="."/>
    </xsl:if>
</xsl:template>

<!--
BIBLIOGRAPHY
-->

<xsl:template match="citation_reference">
    <xref>
        <xsl:attribute name="linkend">
            <xsl:value-of select="@refid"/>
        </xsl:attribute>
        <xsl:attribute name="xml:id">
            <xsl:value-of select="@id"/>
        </xsl:attribute>
    </xref>
</xsl:template>

<xsl:template match="citation"/>

<xsl:template name="bibliography">
<xsl:if test="//citation">
<bibliography>
    <xsl:for-each select="//citation">
        <xsl:apply-templates select="." mode="biblio"/>
    </xsl:for-each>
</bibliography>
</xsl:if>
</xsl:template>

<xsl:template match="citation" mode="biblio">
    <xsl:param name="backrefs" select="@backrefs"/>
    <bibliomixed>
        <xsl:attribute name="xml:id">
            <xsl:value-of select="@id"/>
        </xsl:attribute>
        <xsl:call-template name="backrefs">
            <xsl:with-param name="backrefs" select="$backrefs"/>
            <xsl:with-param name="number" select="1"/>
        </xsl:call-template>
        <xsl:apply-templates select="paragraph" mode="biblio"/>
    </bibliomixed>
</xsl:template>

<xsl:template name="backrefs">
    <xsl:param name="backrefs"/>
    <xsl:param name="number"/>
    <xsl:param name="current_backref">
        <xsl:choose>
            <xsl:when test="contains(normalize-space($backrefs),' ')">
                <xsl:value-of select="substring-before(normalize-space($backrefs),' ')"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="normalize-space($backrefs)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:param>
    <xsl:param name="backrefs_end">
         <xsl:choose>
            <xsl:when test="contains(normalize-space($backrefs),' ')">
                <xsl:value-of select="substring-after(normalize-space($backrefs),' ')"/>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
    </xsl:param>
    <xsl:if test="$number = 1">
        <xsl:value-of select="'('"/>
    </xsl:if>
    <link>
        <xsl:attribute name="linkend">
            <xsl:value-of select="$current_backref"/>
        </xsl:attribute>
        <xsl:value-of select="$number"/>
    </link>
    <xsl:choose>
    <xsl:when test="$backrefs_end!=''">
        <xsl:value-of select="', '"/>
        <xsl:call-template name="backrefs">
             <xsl:with-param name="backrefs" select="$backrefs_end"/>
             <xsl:with-param name="number" select="$number + 1"/>
        </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
        <xsl:value-of select="') '"/>
    </xsl:otherwise>
    </xsl:choose>

</xsl:template>

<xsl:template match="paragraph" mode="biblio">
    <xsl:apply-templates/>
</xsl:template>

<!--
HYPERLINK & FOOTNOTES
-->
<xsl:template match="reference">
    <xsl:choose>
        <xsl:when test="@refuri">
            <xsl:choose>
                <xsl:when test="@internal='True'">
                    <xref>
                        <xsl:attribute name="linkend">
                            <xsl:value-of select="substring-after(@refuri, '#')"/>
                        </xsl:attribute>
                        <!-- Don't apply-templates here or invalid docbook will
                             be generated (<emphasis> in <xref>). -->
                    </xref>
                </xsl:when>
                <xsl:otherwise>
                    <link>
                        <xsl:attribute name="xlink:href">
                            <xsl:value-of select="@refuri"/>
                        </xsl:attribute>
                        <xsl:apply-templates/>
                    </link>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:when>
        <xsl:when test="@refid">
            <link>
                <xsl:attribute name="linkend">
                    <xsl:value-of select="@refid"/>
                </xsl:attribute>
                <xsl:apply-templates/>
            </link>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>

<xsl:template match="footnote"/>

<xsl:template match="footnote" mode="move">
    <footnote>
        <xsl:attribute name="xml:id">
            <xsl:value-of select="@id"/>
        </xsl:attribute>
        <xsl:apply-templates/>
    </footnote>
</xsl:template>

<xsl:template match="footnote/label"/>

<xsl:template match="footnote_reference">
<xsl:param name="footRefNumber"
           select="count(preceding::footnote_reference[@refid=current()/@refid])"/>
    <xsl:choose>
        <xsl:when test="$footRefNumber = 0">
            <xsl:apply-templates select="//footnote[@id=current()/@refid]" mode="move"/>
        </xsl:when>
        <xsl:otherwise>
            <footnoteref>
                <xsl:attribute name="xml:id">
                    <xsl:value-of select="@id"/>
                </xsl:attribute>
                <xsl:attribute name="linkend">
                    <xsl:value-of select="@refid"/>
                </xsl:attribute>
            </footnoteref>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!--
TABLES
-->
<xsl:template match="table">
    <informaltable>
        <xsl:apply-templates/>
    </informaltable>
</xsl:template>

<xsl:template match="tgroup">
    <tgroup>
        <xsl:attribute name="cols">
            <xsl:value-of select="@cols"/>
        </xsl:attribute>
        <xsl:apply-templates/>
    </tgroup>
</xsl:template>

<xsl:template match="colspec">
    <colspec>
        <xsl:attribute name="colwidth">
            <xsl:value-of select="@colwidth"/>
        </xsl:attribute>
    </colspec>
</xsl:template>

<xsl:template match="thead">
    <thead>
        <xsl:apply-templates/>
    </thead>
</xsl:template>

<xsl:template match="tbody">
    <tbody>
        <xsl:apply-templates/>
    </tbody>
</xsl:template>

<xsl:template match="row">
    <row>
        <xsl:apply-templates/>
    </row>
</xsl:template>

<xsl:template match="entry">
    <entry>
        <xsl:if test="@morerows">
            <xsl:attribute name="morerows">
                <xsl:value-of select="@morerows"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:if test="@morecols">
            <xsl:attribute name="morecols">
                <xsl:value-of select="@morecols"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
    </entry>
</xsl:template>

<!--
FIGURES & IMAGES
-->

<xsl:template match="figure">
<figure>
    <xsl:apply-templates select="caption"/>
    <xsl:apply-templates select="image"/>
</figure>
</xsl:template>

<xsl:template match="image">
<mediaobject>
    <imageobject>
        <imagedata>
            <xsl:if test="@uri">
                <xsl:attribute name="fileref">
                    <xsl:value-of select="@uri"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@height">
                <xsl:attribute name="height">
                    <xsl:value-of select="@height"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@width">
                <xsl:attribute name="width">
                    <xsl:value-of select="@width"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@scale">
                <xsl:attribute name="scale">
                    <xsl:value-of select="@scale"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@align='center'
                            or @align='left'
                            or @align='right'">
                <xsl:attribute name="align">
                    <xsl:value-of select="@align"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@align='top'
                            or @align='middle'
                            or @align='bottom' ">
                <xsl:attribute name="valign">
                    <xsl:value-of select="@align"/>
                </xsl:attribute>
            </xsl:if>
         </imagedata>
    </imageobject>
    <xsl:if test="@alt">
        <textobject>
            <xsl:value-of select="@alt"/>
        </textobject>
    </xsl:if>
    <xsl:if test="../legend">
        <xsl:apply-templates select="../legend"/>
    </xsl:if>
</mediaobject>
</xsl:template>

<xsl:template match="caption">
    <title>
        <xsl:apply-templates/>
    </title>
</xsl:template>

<xsl:template match="legend">
    <caption>
        <xsl:apply-templates/>
    </caption>
</xsl:template>


<!--
ADMONITIONS & NOTES
-->

<xsl:template match="note">
    <note>
        <xsl:apply-templates/>
    </note>
</xsl:template>

<xsl:template match="important">
    <important>
        <xsl:apply-templates/>
    </important>
</xsl:template>

<xsl:template match="caution|attention">
    <caution>
        <xsl:if test="name(.)!='caution'">
            <xsl:attribute name="role">
                <xsl:value-of select="name(.)"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
    </caution>
</xsl:template>

<xsl:template match="warning|danger|error">
    <warning>
        <xsl:if test="name(.)!='warning'">
            <xsl:attribute name="role">
                <xsl:value-of select="name(.)"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
    </warning>
</xsl:template>

<xsl:template match="tip|hint">
    <tip>
        <xsl:if test="name(.)!='tip'">
            <xsl:attribute name="role">
                <xsl:value-of select="name(.)"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
    </tip>
</xsl:template>


<!--
OTHER
-->
<xsl:template match="comment">
    <xsl:comment>
        <xsl:value-of select="."/>
    </xsl:comment>
</xsl:template>
<xsl:template match="substitution_definition"/>

</xsl:stylesheet>
